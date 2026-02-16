import subprocess
import psutil
import os
import signal
from typing import Optional, Dict
from config import Config

class ProcessManager:
    """Manage bot processes"""
    
    def __init__(self):
        self.processes: Dict[int, subprocess.Popen] = {}
    
    def start_bot(self, bot_id: int, file_path: str, file_type: str) -> tuple[bool, str, Optional[int]]:
        """
        Start a bot process
        Returns: (success, message, process_id)
        """
        try:
            # Determine command based on file type
            if file_type == 'python':
                cmd = ['python3', file_path]
            elif file_type == 'javascript':
                cmd = ['node', file_path]
            else:
                return False, "❌ Unsupported file type", None
            
            # Start process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.path.dirname(file_path),
                preexec_fn=os.setsid  # Create new process group
            )
            
            self.processes[bot_id] = process
            
            return True, f"✅ Bot started successfully! (PID: {process.pid})", process.pid
            
        except Exception as e:
            return False, f"❌ Failed to start bot: {str(e)}", None
    
    def stop_bot(self, bot_id: int, process_id: int) -> tuple[bool, str]:
        """Stop a bot process"""
        try:
            if bot_id in self.processes:
                process = self.processes[bot_id]
                
                # Kill process group
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                process.wait(timeout=5)
                
                del self.processes[bot_id]
                return True, "✅ Bot stopped successfully!"
            else:
                # Try to kill by PID
                if psutil.pid_exists(process_id):
                    process = psutil.Process(process_id)
                    process.terminate()
                    process.wait(timeout=5)
                    return True, "✅ Bot stopped successfully!"
                else:
                    return False, "❌ Process not found"
                    
        except subprocess.TimeoutExpired:
            # Force kill if timeout
            if bot_id in self.processes:
                self.processes[bot_id].kill()
                del self.processes[bot_id]
            return True, "✅ Bot force stopped!"
        except Exception as e:
            return False, f"❌ Failed to stop bot: {str(e)}"
    
    def restart_bot(self, bot_id: int, process_id: int, file_path: str, file_type: str) -> tuple[bool, str, Optional[int]]:
        """Restart a bot"""
        # Stop first
        self.stop_bot(bot_id, process_id)
        
        # Start again
        return self.start_bot(bot_id, file_path, file_type)
    
    def get_bot_status(self, bot_id: int, process_id: int) -> Dict:
        """Get bot process status"""
        try:
            if psutil.pid_exists(process_id):
                process = psutil.Process(process_id)
                return {
                    'running': True,
                    'cpu_percent': process.cpu_percent(),
                    'memory_mb': process.memory_info().rss / 1024 / 1024,
                    'status': process.status()
                }
            else:
                return {'running': False}
        except:
            return {'running': False}
    
    def get_bot_logs(self, bot_id: int) -> str:
        """Get bot stdout/stderr"""
        if bot_id in self.processes:
            process = self.processes[bot_id]
            stdout, stderr = process.communicate(timeout=1)
            
            logs = ""
            if stdout:
                logs += f"**STDOUT:**\n```\n{stdout.decode()}\n```\n\n"
            if stderr:
                logs += f"**STDERR:**\n```\n{stderr.decode()}\n```"
            
            return logs if logs else "No logs available"
        return "Process not found"
    
    def install_module(self, module_name: str) -> tuple[bool, str]:
        """Install a Python module"""
        try:
            result = subprocess.run(
                ['pip', 'install', module_name],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if result.returncode == 0:
                return True, f"✅ Module '{module_name}' installed successfully!"
            else:
                return False, f"❌ Installation failed:\n```\n{result.stderr}\n```"
                
        except subprocess.TimeoutExpired:
            return False, "❌ Installation timeout (5 minutes)"
        except Exception as e:
            return False, f"❌ Error: {str(e)}"

# Global process manager
process_manager = ProcessManager()
