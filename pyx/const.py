
# align constants

left = "left"
center = "center"
right = "right"
top = "top"
bottom = "bottom"

# helper stuff TODO: discuss this, create helper module?

def isnumber(x):
    import types
    if x is not types.IntType and x is not types.FloatType:
        assert "number expected"

