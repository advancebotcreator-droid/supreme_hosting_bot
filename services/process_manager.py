"""
Supreme Hosting Bot - Process Manager
Manages subprocess lifecycle for hosted bots
"""

import asyncio
import os
import signal
import sys
import time
from typing import Dict, Optional, Callable, Awaitable
from collections import deque

from config import LOGS_DIR


class ManagedProcess:
    """Represents a single managed subprocess."""
    
    def __init__(self, bot_id: int, file_path: str, working_dir: str):
        self.bot_id = bot_id
        self.file_path = file_path
        self.working_dir = working_dir
        self.process: Optional[asyncio.subprocess.Process] = None
        self.pid: int = 0
        self.log_buffer: deque = deque(maxlen=200)
        self._stdout_task: Optional[asyncio.Task] = None
        self._stderr_task: Optional[asyncio.Task] = None
        self._log_callback: Optional[Callable] = None

    @property
    def is_running(self) -> bool:
        return self.process is not None and self.process.returncode is None


class ProcessManager:
    """Manages all hosted bot processes."""
    
    def __init__(self):
        self._processes: Dict[int, ManagedProcess] = {}
        self._log_callback: Optional[Callable] = None

    def set_log_callback(self, callback: Callable[[int, str, str], Awaitable[None]]):
        """Set callback for logging: callback(bot_id, message, log_type)"""
        self._log_callback = callback

    async def start_process(self, bot_id: int, file_path: str, working_dir: str) -> tuple:
        """
        Start a bot process.
        Returns: (success: bool, message: str, pid: int)
        """
        # Kill existing process if any
        if bot_id in self._processes:
            await self.stop_process(bot_id)

        if not os.path.exists(file_path):
            return False, "File not found!", 0

        try:
            # Determine the interpreter
            if file_path.endswith('.py'):
                cmd = [sys.executable, '-u', file_path]
            elif file_path.endswith('.js'):
                cmd = ['node', file_path]
            else:
                cmd = [sys.executable, '-u', file_path]

            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'
            env['PYTHONIOENCODING'] = 'utf-8'

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir,
                env=env,
                preexec_fn=os.setsid if hasattr(os, 'setsid') else None
            )

            managed = ManagedProcess(bot_id, file_path, working_dir)
            managed.process = process
            managed.pid = process.pid

            # Start log readers
            managed._stdout_task = asyncio.create_task(
                self._read_stream(bot_id, process.stdout, "stdout")
            )
            managed._stderr_task = asyncio.create_task(
                self._read_stream(bot_id, process.stderr, "stderr")
            )

            self._processes[bot_id] = managed

            return True, "Process started successfully", process.pid

        except FileNotFoundError:
            return False, "Python interpreter not found", 0
        except PermissionError:
            return False, "Permission denied", 0
        except Exception as e:
            return False, f"Failed to start: {str(e)}", 0

    async def stop_process(self, bot_id: int) -> tuple:
        """
        Stop a bot process.
        Returns: (success: bool, message: str)
        """
        managed = self._processes.get(bot_id)
        if not managed:
            return True, "No process found (already stopped)"

        try:
            if managed.process and managed.process.returncode is None:
                # Try graceful termination first
                try:
                    if hasattr(os, 'killpg'):
                        os.killpg(os.getpgid(managed.process.pid), signal.SIGTERM)
                    else:
                        managed.process.terminate()
                except (ProcessLookupError, OSError):
                    pass

                try:
                    await asyncio.wait_for(managed.process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    # Force kill
                    try:
                        if hasattr(os, 'killpg'):
                            os.killpg(os.getpgid(managed.process.pid), signal.SIGKILL)
                        else:
                            managed.process.kill()
                    except (ProcessLookupError, OSError):
                        pass
                    try:
                        await asyncio.wait_for(managed.process.wait(), timeout=3.0)
                    except asyncio.TimeoutError:
                        pass

            # Cancel log tasks
            for task in [managed._stdout_task, managed._stderr_task]:
                if task and not task.done():
                    task.cancel()
                    try:
                        await task
                    except (asyncio.CancelledError, Exception):
                        pass

            del self._processes[bot_id]
            return True, "Process stopped"

        except Exception as e:
            # Clean up anyway
            self._processes.pop(bot_id, None)
            return True, f"Stopped with warning: {str(e)}"

    async def restart_process(self, bot_id: int) -> tuple:
        """Restart a bot process."""
        managed = self._processes.get(bot_id)
        if not managed:
            return False, "No process info found. Start the bot first.", 0

        file_path = managed.file_path
        working_dir = managed.working_dir
        
        await self.stop_process(bot_id)
        await asyncio.sleep(1)
        return await self.start_process(bot_id, file_path, working_dir)

    def is_running(self, bot_id: int) -> bool:
        managed = self._processes.get(bot_id)
        return managed is not None and managed.is_running

    def get_pid(self, bot_id: int) -> int:
        managed = self._processes.get(bot_id)
        return managed.pid if managed else 0

    def get_recent_logs(self, bot_id: int, count: int = 50) -> list:
        managed = self._processes.get(bot_id)
        if managed:
            return list(managed.log_buffer)[-count:]
        return []

    def get_running_count(self) -> int:
        return sum(1 for m in self._processes.values() if m.is_running)

    async def stop_all(self) -> int:
        """Stop all running processes. Returns count stopped."""
        count = 0
        bot_ids = list(self._processes.keys())
        for bot_id in bot_ids:
            success, _ = await self.stop_process(bot_id)
            if success:
                count += 1
        return count

    async def _read_stream(self, bot_id: int, stream, log_type: str):
        """Read from subprocess stream and buffer logs."""
        try:
            while True:
                line = await stream.readline()
                if not line:
                    break
                decoded = line.decode('utf-8', errors='replace').rstrip()
                if decoded:
                    managed = self._processes.get(bot_id)
                    if managed:
                        timestamp = time.strftime("%H:%M:%S")
                        prefix = "OUT" if log_type == "stdout" else "ERR"
                        log_entry = f"[{timestamp}][{prefix}] {decoded}"
                        managed.log_buffer.append(log_entry)
                    
                    if self._log_callback:
                        try:
                            await self._log_callback(bot_id, decoded, log_type)
                        except Exception:
                            pass
        except asyncio.CancelledError:
            pass
        except Exception:
            pass


# Global process manager instance
process_manager = ProcessManager()
