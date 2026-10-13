#!/usr/bin/env python3
"""跨平台 skill 入口：统一参数、能力校验和写入前的路径保护。"""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import unicodedata


REQUIRED_ENGINE_CAPABILITIES = (
    "fresh-execution", "children-syntax", "competing-children-syntax",
    "scope-variables", "external-language-dependencies", "syntax-contexts",
    "line-backgrounds", "structured-highlighting", "highlight-position-query",
    "inspection-fingerprints", "highlight-diff", "sample-assertions",
    "batch-validation", "rule-explanation", "rule-coverage", "sample-benchmark",
    "benchmark-diff", "benchmark-suite", "benchmark-suite-diff",
)
OUTPUT_MODES = {
    "--html": None,
    "--inspect-json": "--inspect",
    "--explain-json": "--explain",
    "--coverage-json": "--coverage",
    "--benchmark-json": "--benchmark",
    "--diff-json": "--diff",
    "--benchmark-diff-json": "--benchmark-diff",
    "--benchmark-suite-diff-json": "--benchmark-suite-diff",
    "--suite-json": "--suite",
    "--benchmark-suite-json": "--benchmark-suite",
}
FLAGS = {"--check-only", "--coverage"}
QUERIES = {"--at", "--position", "--range"}
VALUES = set(OUTPUT_MODES) | QUERIES | {
    "--jar", "--syntax-file", "--syntax-dependency", "--sample-file", "--code",
    "--report", "--warmup", "--iterations", "--before", "--after", "--max-details",
    "--suite", "--benchmark-suite",
}


class UsageError(ValueError):
    """参数或路径冲突在启动 Java 前失败，禁止产生报告副作用。"""


def parse_arguments(arguments):
    """单值沿用最后一次值，依赖与查询保留原序；代码允许空串和 -- 前缀。"""
    values, dependencies, queries = {}, [], []
    index = 0
    while index < len(arguments):
        option = arguments[index]
        index += 1
        if option in FLAGS:
            values[option] = True
            continue
        if option not in VALUES:
            raise UsageError("Unknown argument: " + option)
        if index == len(arguments):
            raise UsageError("Missing value for " + option)
        value = arguments[index]
        index += 1
        if option != "--code" and (not value or value.startswith("--")):
            raise UsageError("Missing value for " + option)
        if option == "--syntax-dependency":
            dependencies.append(value)
        elif option in QUERIES:
            queries.extend((option, value))
        else:
            values[option] = value
    return values, dependencies, queries


def build_command(values, dependencies, queries):
    """各模式只接受自己消费的选项，后端继续校验坐标、清单和数值范围。"""
    outputs = [option for option in OUTPUT_MODES if option in values]
    if len(outputs) > 1 or (outputs and "--check-only" in values):
        raise UsageError("Cannot combine output modes")
    if "--report" not in values:
        raise UsageError("Missing --report")
    output = outputs[0] if outputs else None
    mode = OUTPUT_MODES[output] if output else "--check"
    if not output and "--check-only" not in values:
        raise UsageError("Missing output mode or --check-only")

    allowed = {"--jar", "--report", output} if output else {"--jar", "--report", "--check-only"}
    tail = []
    if mode in ("--suite", "--benchmark-suite"):
        allowed.add(mode)
        if mode not in values:
            raise UsageError("Missing " + mode)
        tail.extend((mode, values[mode]))
        if mode == "--suite":
            allowed.add("--coverage")
            if "--coverage" in values:
                tail.append("--coverage")
    elif mode in ("--diff", "--benchmark-diff", "--benchmark-suite-diff"):
        allowed.update(("--before", "--after"))
        if "--before" not in values or "--after" not in values:
            raise UsageError("Comparison requires --before and --after")
        tail.extend((mode, "--before", values["--before"], "--after", values["--after"]))
        if mode == "--diff":
            allowed.add("--max-details")
            if "--max-details" in values:
                tail.extend(("--max-details", values["--max-details"]))
    else:
        allowed.update(("--syntax-file", "--sample-file", "--code"))
        if "--syntax-file" not in values:
            raise UsageError("Missing --syntax-file")
        if "--sample-file" in values and "--code" in values:
            raise UsageError("--sample-file and --code are mutually exclusive")
        if mode != "--check" and not {"--sample-file", "--code"} & values.keys():
            raise UsageError("Render mode requires --sample-file or --code")
        tail.extend(("--syntax-file", values["--syntax-file"]))
        for dependency in dependencies:
            tail.extend(("--syntax-dependency", dependency))
        if "--sample-file" in values:
            tail.extend(("--input", values["--sample-file"]))
        elif "--code" in values:
            tail.extend(("--code", values["--code"]))
        if mode:
            tail.append(mode)
        if mode == "--coverage":
            allowed.add("--coverage")
        if mode == "--benchmark":
            allowed.update(("--warmup", "--iterations"))
            for option in ("--warmup", "--iterations"):
                if option in values:
                    tail.extend((option, values[option]))
        if mode in ("--inspect", "--explain"):
            tail.extend(queries)
        if mode == "--explain":
            allowed.add("--max-details")
            if "--max-details" in values:
                tail.extend(("--max-details", values["--max-details"]))

    # 批量和比较模式不接受单例依赖；查询只属于 inspection/explanation。
    if dependencies and mode in ("--suite", "--benchmark-suite", "--diff", "--benchmark-diff", "--benchmark-suite-diff"):
        raise UsageError("This mode does not accept --syntax-dependency")
    if queries and mode not in ("--inspect", "--explain"):
        raise UsageError("--at, --position and --range require --inspect-json or --explain-json")
    unexpected = values.keys() - allowed
    if unexpected:
        raise UsageError("Options not supported by this mode: " + ", ".join(sorted(unexpected)))
    if output:
        tail.extend(("--output", values[output]))
    tail.extend(("--report", values["--report"]))
    jar = values.get("--jar", str(Path(__file__).resolve().parent.parent / "lib" / "mt-syntax.jar"))
    return ["java", "-jar", jar] + tail, output


def comparison_key(path):
    """先解析链接与 ..；macOS/Windows 沿用保守的名称折叠，Linux 保留大小写。"""
    real = os.path.realpath(path)
    if sys.platform in ("darwin", "win32"):
        return unicodedata.normalize("NFD", real).casefold()
    return real


def aliases(first, second):
    if comparison_key(first) == comparison_key(second):
        return True
    try:
        return os.path.samefile(first, second)
    except OSError:
        return False


def validate_artifact_paths(values, dependencies, jar, output):
    """--jar 被入口消费，必须在这里保护；清单内部引用继续由后端枚举。"""
    readers = [("--jar", jar)]
    readers.extend((option, values[option]) for option in (
        "--syntax-file", "--sample-file", "--before", "--after", "--suite", "--benchmark-suite"
    ) if option in values)
    readers.extend(("--syntax-dependency", path) for path in dependencies)
    writers = [("--report", values["--report"])]
    if output:
        writers.append((output, values[output]))
    for writer, destination in writers:
        for reader, source in readers:
            if aliases(destination, source):
                raise UsageError("Path conflict: {} must differ from {}: {}".format(writer, reader, destination))
    if output and aliases(values["--report"], values[output]):
        raise UsageError("Path conflict: --report must differ from {}: {}".format(output, values["--report"]))


_WINDOWS_JOB = None


def protect_windows_process_tree():
    """先把入口加入不可脱离的 Job，子进程从创建时起继承，强制结束入口也能清理。"""
    global _WINDOWS_JOB
    if sys.platform != "win32" or _WINDOWS_JOB is not None:
        return
    import ctypes
    from ctypes import wintypes

    class BasicLimits(ctypes.Structure):
        _fields_ = [("PerProcessUserTimeLimit", ctypes.c_longlong),
                    ("PerJobUserTimeLimit", ctypes.c_longlong),
                    ("LimitFlags", wintypes.DWORD),
                    ("MinimumWorkingSetSize", ctypes.c_size_t),
                    ("MaximumWorkingSetSize", ctypes.c_size_t),
                    ("ActiveProcessLimit", wintypes.DWORD),
                    ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD),
                    ("SchedulingClass", wintypes.DWORD)]

    class ExtendedLimits(ctypes.Structure):
        _fields_ = [("BasicLimitInformation", BasicLimits),
                    ("IoInfo", ctypes.c_ulonglong * 6),
                    ("ProcessMemoryLimit", ctypes.c_size_t),
                    ("JobMemoryLimit", ctypes.c_size_t),
                    ("PeakProcessMemoryUsed", ctypes.c_size_t),
                    ("PeakJobMemoryUsed", ctypes.c_size_t)]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateJobObjectW.argtypes = (ctypes.c_void_p, wintypes.LPCWSTR)
    kernel.CreateJobObjectW.restype = wintypes.HANDLE
    kernel.SetInformationJobObject.argtypes = (wintypes.HANDLE, ctypes.c_int,
                                               ctypes.c_void_p, wintypes.DWORD)
    kernel.SetInformationJobObject.restype = wintypes.BOOL
    kernel.GetCurrentProcess.argtypes = ()
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.AssignProcessToJobObject.argtypes = (wintypes.HANDLE, wintypes.HANDLE)
    kernel.AssignProcessToJobObject.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel.CloseHandle.restype = wintypes.BOOL
    job = kernel.CreateJobObjectW(None, None)  # 默认不可继承，子进程不能延长 Job 句柄寿命。
    if not job:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        limits = ExtendedLimits()
        limits.BasicLimitInformation.LimitFlags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not kernel.SetInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            raise ctypes.WinError(ctypes.get_last_error())
        if not kernel.AssignProcessToJobObject(job, kernel.GetCurrentProcess()):
            raise ctypes.WinError(ctypes.get_last_error())
    except BaseException:
        kernel.CloseHandle(job)
        raise
    # Job 包含入口自身，不能提前 CloseHandle；由系统在入口退出时关闭并清理后代。
    _WINDOWS_JOB = job


class Cancelled(Exception):
    """取消独立于引擎失败，沿用 128 + signal 的退出码。"""

    def __init__(self, signum):
        self.returncode = 128 + signum


class JavaRunner:
    """主线程专用；监督元数据检查及 Windows 执行，POSIX 正式执行替换当前进程。"""

    def __init__(self):
        self.cancel_signal = None
        self.previous_handlers = {}

    def __enter__(self):
        signals = [signal.SIGINT, signal.SIGTERM]
        signals.append(signal.SIGBREAK if sys.platform == "win32" else signal.SIGHUP)
        for signum in signals:
            self.previous_handlers[signum] = signal.signal(signum, self.cancel)
        try:
            protect_windows_process_tree()
        except BaseException:
            self.__exit__(None, None, None)
            raise
        return self

    def __exit__(self, *unused):
        for signum, handler in self.previous_handlers.items():
            signal.signal(signum, handler)

    def cancel(self, signum, frame):
        # 只记录，不从 Popen 构造中抛出异常，避免已创建子进程却丢失其句柄。
        if self.cancel_signal is None:
            self.cancel_signal = signum

    def check_cancelled(self):
        if self.cancel_signal is not None:
            raise Cancelled(self.cancel_signal)

    def execute(self, command):
        """POSIX 保持 Java 与入口同 PID，调用方硬超时直接结束 Java；Windows 保留 Job。"""
        self.check_cancelled()
        if sys.platform == "win32":
            return self.run(command).returncode
        # 交接时先恢复默认动作，再检查已记录的取消；避免最后检查后吞掉信号再启动 Java。
        for signum in self.previous_handlers:
            signal.signal(signum, signal.SIG_DFL)
        self.check_cancelled()
        os.execvp(command[0], command)

    def run(self, command, capture=False):
        self.check_cancelled()
        process = subprocess.Popen(command, stdout=subprocess.PIPE if capture else None,
                                   encoding="utf-8", errors="strict")
        try:
            while True:
                self.check_cancelled()
                try:
                    # Windows 阻塞等待期间不保证及时执行 Python 信号处理器，定期让出等待。
                    stdout, _ = process.communicate(timeout=0.1)
                    self.check_cancelled()
                    return subprocess.CompletedProcess(command, process.returncode, stdout)
                except subprocess.TimeoutExpired:
                    pass
        finally:
            # 取消不能依赖 Java 响应中断或 shutdown hook，防止继续发布文件。
            if process.poll() is None:
                process.kill()
            process.wait()
            if process.stdout is not None:
                process.stdout.close()


def check_engine_capabilities(command, runner):
    """仅元数据捕获为 UTF-8；正式命令继承终端，不经过 shell 拼接参数。"""
    result = runner.run(command[:3] + ["--engine-info"], capture=True)
    if result.returncode:
        raise RuntimeError("Unable to query validator engine metadata: " + command[2])
    line = result.stdout.rstrip("\r\n")
    if not line or "\n" in line or "\r" in line:
        raise RuntimeError("Validator --engine-info must return one non-empty JSON line")
    try:
        info = json.loads(line)
        if not isinstance(info, dict):
            raise ValueError("root must be an object")
        if not isinstance(info.get("upstreamCommit"), str) or not info["upstreamCommit"]:
            raise ValueError("missing upstreamCommit")
        capabilities = info.get("capabilities")
        if not isinstance(capabilities, list) or not all(isinstance(item, str) for item in capabilities):
            raise ValueError("capabilities must be a string array")
        missing = [item for item in REQUIRED_ENGINE_CAPABILITIES if item not in capabilities]
        if missing:
            raise ValueError("missing capabilities: " + ", ".join(missing))
    except ValueError as exc:
        raise RuntimeError("Incompatible validator engine: " + str(exc)) from exc


def main(arguments=None):
    try:
        # Windows realpath 自 3.8 起解析符号链接和 junction，路径保护依赖该行为。
        if sys.version_info < (3, 6) or (sys.platform == "win32" and sys.version_info < (3, 8)):
            raise RuntimeError("Requires Python 3.6+ (Python 3.8+ on Windows)")
        values, dependencies, queries = parse_arguments(sys.argv[1:] if arguments is None else arguments)
        command, output = build_command(values, dependencies, queries)
        validate_artifact_paths(values, dependencies, command[2], output)
        with JavaRunner() as runner:
            check_engine_capabilities(command, runner)
            result = runner.execute(command)
        return result if result >= 0 else 128 - result
    except Cancelled as exc:
        return exc.returncode
    except UsageError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except (OSError, RuntimeError, UnicodeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
