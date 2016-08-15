import sys, tty, termios
from abc import ABCMeta, abstractmethod
import traceback

class ShellInterface(object):
    __metaclass__ = ABCMeta
    def __init__(self, echo=True, output="True", prompt="", welcome="", bye=""):
        self.prompt = prompt
        self.welcome = welcome
        self.bye = bye
        self.echo = echo
        self.output = output

    @abstractmethod
    def processLine(self, inputLine):
        raise NotImplementedError

class Shell(ShellInterface):
    def __init__(self, *args, **kwargs):
        super(Shell, self).__init__(*args, **kwargs)
        self._chars = []
        self._history = []
        self._last1 = None
        self._last2 = None
        self._last3 = None
        self._cursor = 0
        self._histIdx = 0

    def start(self):
        if self.welcome:
            print self.welcome
        sys.stdout.write(self.prompt)
        while True:
            try:
                fd = sys.stdin.fileno()
                oldsettings = termios.tcgetattr(fd)
                tty.setraw(sys.stdin.fileno())
                c = sys.stdin.read(1)
                termios.tcsetattr(fd, termios.TCSADRAIN, oldsettings)
                self._processChar(c)
            except KeyboardInterrupt:
                print
                break
            except:
                print traceback.format_exc()
                break
        if self.bye:
            print self.bye

    def _resetLast(self):
        self._last1 = None
        self._last2 = None
        self._last3 = None

    def _backspace(self):
        if self._cursor > 0:
            self._cursor -= 1
            self._chars.pop(self._cursor)
            if self.echo:
                sys.stdout.write("\r\033[K")
                sys.stdout.write(self.prompt + "".join([i for i in self._chars]))
                offset = len(self._chars) - self._cursor
                if offset:
                    sys.stdout.write("\033[%dD" % offset)
        
    def _delete(self):
        if self._cursor < len(self._chars):
            self._chars.pop(self._cursor)
            if self.echo:
                sys.stdout.write("\r\033[K")
                sys.stdout.write(self.prompt + "".join([i for i in self._chars]))
                offset = len(self._chars) - self._cursor
                if offset:
                    sys.stdout.write("\033[%dD" % offset)

    def _write(self, c):
        if self._cursor < len(self._chars):
            self._chars.insert(self._cursor, c)
            offset = len(self._chars) - self._cursor - 1
            if self.echo:
                sys.stdout.write("\r\033[K")
                sys.stdout.write(self.prompt + "".join([i for i in self._chars]))
                sys.stdout.write("\033[%dD" % offset)
        else:
            self._chars.append(c)
            if self.echo:
                sys.stdout.write(c)
        self._cursor += 1
        
    def _process(self, c):
        self._write(c)
        self._last1 = self._last2
        self._last2 = self._last1
        self._last3 = ord(c)

    def _enter(self):
        line = "".join(self._chars)
        self._cursor = 0
        self._history.append(line)
        self._histIdx = len(self._history)
        del self._chars[:]
        if self.echo:
            sys.stdout.write("\n")
        for output in self.processLine(line):
            if self.output:
                print output
        sys.stdout.write(self.prompt)

    def _hist(self, idx):
        del self._chars[:]
        self._chars = [i for i in self._history[idx]]
        if self.echo:
            sys.stdout.write("\r\033[K")
            sys.stdout.write(self.prompt)
            sys.stdout.write(self._history[idx])
        self._cursor = len(self._chars)

    def _upArrow(self):
        if self._histIdx:
            self._hist(self._histIdx - 1)
            self._histIdx -= 1
        self._resetLast()

    def _downArrow(self):
        if self._histIdx + 1 < len(self._history):
            self._histIdx += 1
            self._hist(self._histIdx)
        self._resetLast()

    def _leftArrow(self):
        if self._cursor > 0:
            self._cursor -= 1
            if self.echo:
                sys.stdout.write("\033[1D")
        self._resetLast()

    def _rightArrow(self):
        if self._cursor < len(self._chars):
            self._cursor += 1
            if self.echo:
                sys.stdout.write("\033[1C")
        self._resetLast()

    def _notArrow(self, c):
        self._write(chr(self._last1))
        self._write(chr(self._last2))
        self._process(c)

    def _notDelete(self, c):
        self._write(chr(self._last1))
        self._write(chr(self._last2))
        self._write(chr(self._last3))
        self._process(c)

    def _processChar(self, c):
        ordc = ord(c)
        if ordc in (3, 4):
            raise KeyboardInterrupt
        if (ordc == 10) or (ordc == 13):
            self._enter()
            return self._resetLast()
        elif ordc in (8, 127):
            self._backspace()
            return self._resetLast()
        elif self._last1 == 27:
            if self._last2 == 91:
                if self._last3 == 51:
                    if ordc == 126:
                        self._delete()
                        return self._resetLast()
            return _notDelete(c)
        elif self._last2 == 27:
            if self._last3 == 91:
                if ordc == 51:
                    self._last1 = 27
                    self._last2 = 91
                    self._last3 = 51
                    return
                if ordc == 65:
                    return self._upArrow()
                if ordc == 66:
                    return self._downArrow()
                if ordc == 67:
                    return self._rightArrow()
                if ordc == 68:
                    return self._leftArrow()
            return self._notArrow(c)
        elif self._last3 == 27:
            if ordc == 91:
                self._last1 = None
                self._last2 = 27
                self._last3 = 91
                return
            return self._process(c)
        elif ordc == 27:
            self._last1 = None
            self._last2 = None
            self._last3 = 27
            return
        return self._process(c)

def test():
    class TestShell(Shell):
        def processLine(self, line):
            return iter(())

    s = TestShell(output=False, echo=False)
    for c in "1\n2\n3\n4\n5\n":
        s._processChar(c)
    for i, c in enumerate("12345"):
        assert s._history[i] == c
        print "History test passed, i = %d, c = %s :)" % (i, c) 

    for i, c in enumerate("54321"):
        s._processChar(chr(27))
        s._processChar(chr(91))
        s._processChar(chr(65))
        assert s._histIdx == 4 - i
        assert s._chars == [c]
    s._processChar(chr(27))
    s._processChar(chr(91))
    s._processChar(chr(65))
    assert s._histIdx == 0
    assert s._chars == ['1']
    print "Up arrow key tests passed :)"

    for i, c in enumerate("12345"):
        assert s._histIdx == i
        assert s._chars == [c]
        s._processChar(chr(27))
        s._processChar(chr(91))
        s._processChar(chr(66))
    assert s._histIdx == 4
    assert s._chars == ['5']
    s._processChar(chr(27))
    s._processChar(chr(91))
    s._processChar(chr(66))
    assert s._histIdx == 4
    assert s._chars == ['5']
    print "Down arrow key tests passed :)"

    s._processChar(chr(27))
    s._processChar(chr(91))
    s._processChar(chr(68))
    s._processChar('0')
    assert s._chars == ['0', '5']
    s._processChar(chr(27))
    s._processChar(chr(91))
    s._processChar(chr(68))
    s._processChar('1')
    assert s._chars == ['1', '0', '5']
    s._processChar('1')
    s._processChar('1')
    s._processChar(chr(27))
    s._processChar(chr(91))
    s._processChar(chr(68))
    s._processChar('0')
    assert s._chars == ['1', '1', '0', '1', '0', '5']
    print "Left arrow key tests passed :)"

    s._processChar(chr(27))
    s._processChar(chr(91))
    s._processChar(chr(67))
    s._processChar('0')
    assert s._chars == ['1', '1', '0', '1', '0', '0', '5']
    s._processChar(chr(27))
    s._processChar(chr(91))
    s._processChar(chr(67))
    s._processChar(chr(27))
    s._processChar(chr(91))
    s._processChar(chr(67))
    s._processChar('0')
    assert s._chars == ['1', '1', '0', '1', '0', '0', '5', '0']
    s._processChar(chr(27))
    s._processChar(chr(91))
    s._processChar(chr(67))
    s._processChar('0')
    assert s._chars == ['1', '1', '0', '1', '0', '0', '5', '0', '0']
    print "Right arrow key tests passed :)"

    s._processChar('\b')
    assert s._chars == ['1', '1', '0', '1', '0', '0', '5', '0']
    s._processChar('\b')
    assert s._chars == ['1', '1', '0', '1', '0', '0', '5']
    s._processChar(chr(27))
    s._processChar(chr(91))
    s._processChar(chr(68))
    s._processChar('\b')
    s._processChar('\b')
    assert s._chars == ['1', '1', '0', '1', '5']
    s._processChar('\b')
    s._processChar('\b')
    s._processChar('\b')
    s._processChar('\b')
    assert s._chars == ['5']
    s._processChar('\b')
    assert s._chars == ['5']
    print "Backspace tests passed :)"

    s._processChar(chr(27))
    s._processChar(chr(91))
    s._processChar(chr(51))
    s._processChar(chr(126))
    assert s._chars == []
    s._processChar(chr(27))
    s._processChar(chr(91))
    s._processChar(chr(51))
    s._processChar(chr(126))
    assert s._chars == []
    print "Delete tests passed :)"
    
    s._processChar("a")
    s._processChar("b")
    s._processChar("c")
    s._processChar("d")
    s._processChar("e")
    s._processChar("\n")
    s._processChar(chr(27))
    s._processChar(chr(91))
    s._processChar(chr(65))
    assert s._chars == ['a', 'b', 'c', 'd', 'e']
    assert s._cursor == 5
    s._processChar(chr(27))
    s._processChar(chr(91))
    s._processChar(chr(68))
    assert s._cursor == 4
    print "All tests passed :)"

def interact():
    class EchoShell(Shell):
        def processLine(self, line):
            return line

    EchoShell(prompt='es > ').start()

if __name__ == '__main__':
    test()
    interact()
