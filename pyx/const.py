
# align constants

left = "left"
center = "center"
right = "right"
top = "top"
bottom = "bottom"

# helper stuff TODO: discuss this, create helper module?

def isnumber(x):
    import types
    if type(x) in [types.IntType, types.FloatType]:
        return 1
    return 0

