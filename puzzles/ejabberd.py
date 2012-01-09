import shutil
import stat
import subprocess
import os
import os.path
import tempfile

class ejabberdctl:
    def __enter__(self):
        self.dir = tempfile.mkdtemp()
        cookie_file = os.path.join(self.dir, '.erlang.cookie')
        shutil.copyfile('/var/run/ejabberd.erlang.cookie', cookie_file)
        os.chmod(cookie_file, stat.S_IRUSR | stat.S_IWUSR)
        return lambda *args: self.execute(*args)

    def __exit__(self, exc_type, exc_value, traceback):
        shutil.rmtree(self.dir)

    def execute(self, *args):
        subprocess.call(['env', 'HOME=' + self.dir, 'ejabberdctl', '--concurrent'] + list(args))
