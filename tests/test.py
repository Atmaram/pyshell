from pyconsole.shell import Shell

s = None
class TestShell(Shell):
    def processLine(self, line):
        return iter(())

def setup():
    global s
    s = TestShell(output=False, echo=False)
    for c in "1\n2\n3\n4\n5\n":
        s._processChar(c)
    
def teardown():
    global s
    del s
    s = None

def test_history():
    for i, c in enumerate("12345"):
        assert s._history[i] == c

def test_upArrow1():
    for i, c in enumerate("54321"):
        s._processChar(chr(27))
        s._processChar(chr(91))
        s._processChar(chr(65))
        assert s._histIdx == 4 - i
        assert s._chars == [c]

def test_upArrow2():
    s._processChar(chr(27))
    s._processChar(chr(91))
    s._processChar(chr(65))
    assert s._histIdx == 0
    assert s._chars == ['1']

def test_downArrow1():
    for i, c in enumerate("12345"):
        assert s._histIdx == i
        assert s._chars == [c]
        s._processChar(chr(27))
        s._processChar(chr(91))
        s._processChar(chr(66))
    assert s._histIdx == 4
    assert s._chars == ['5']

def test_downArrow2():
    s._processChar(chr(27))
    s._processChar(chr(91))
    s._processChar(chr(66))
    assert s._histIdx == 4
    assert s._chars == ['5']

def test_leftArrow1():
    s._processChar(chr(27))
    s._processChar(chr(91))
    s._processChar(chr(68))
    s._processChar('0')
    assert s._chars == ['0', '5']

def test_leftArrow2():
    s._processChar(chr(27))
    s._processChar(chr(91))
    s._processChar(chr(68))
    s._processChar('1')
    assert s._chars == ['1', '0', '5']

def test_leftArrow3():
    s._processChar('1')
    s._processChar('1')
    s._processChar(chr(27))
    s._processChar(chr(91))
    s._processChar(chr(68))
    s._processChar('0')
    assert s._chars == ['1', '1', '0', '1', '0', '5']

def test_rightArrow1():
    s._processChar(chr(27))
    s._processChar(chr(91))
    s._processChar(chr(67))
    s._processChar('0')
    assert s._chars == ['1', '1', '0', '1', '0', '0', '5']

def test_rightArrow2():
    s._processChar(chr(27))
    s._processChar(chr(91))
    s._processChar(chr(67))
    s._processChar(chr(27))
    s._processChar(chr(91))
    s._processChar(chr(67))
    s._processChar('0')
    assert s._chars == ['1', '1', '0', '1', '0', '0', '5', '0']

def test_rightArrow3():
    s._processChar(chr(27))
    s._processChar(chr(91))
    s._processChar(chr(67))
    s._processChar('0')
    assert s._chars == ['1', '1', '0', '1', '0', '0', '5', '0', '0']

def test_backspace1():
    s._processChar('\b')
    assert s._chars == ['1', '1', '0', '1', '0', '0', '5', '0']

def test_backspace2():
    s._processChar('\b')
    assert s._chars == ['1', '1', '0', '1', '0', '0', '5']

def test_backspace3():
    s._processChar(chr(27))
    s._processChar(chr(91))
    s._processChar(chr(68))
    s._processChar('\b')
    s._processChar('\b')
    assert s._chars == ['1', '1', '0', '1', '5']

def test_backspace4():
    s._processChar('\b')
    s._processChar('\b')
    s._processChar('\b')
    s._processChar('\b')
    assert s._chars == ['5']

def test_backspace5():
    s._processChar('\b')
    assert s._chars == ['5']

def test_delete1():
    s._processChar(chr(27))
    s._processChar(chr(91))
    s._processChar(chr(51))
    s._processChar(chr(126))
    assert s._chars == []

def test_delete2():
    s._processChar(chr(27))
    s._processChar(chr(91))
    s._processChar(chr(51))
    s._processChar(chr(126))
    assert s._chars == []

def test_misc1():
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

def test_misc2():
    s._processChar(chr(27))
    s._processChar(chr(91))
    s._processChar(chr(68))
    assert s._cursor == 4
