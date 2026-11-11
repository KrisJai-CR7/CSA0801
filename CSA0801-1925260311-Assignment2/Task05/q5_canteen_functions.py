"""
Q5 - Functions, Parameters and Scope (College Canteen Order System)
Bug: add_item(item, order=[]) - the default list is created ONCE, when the
function is defined, and is then shared by every call that omits `order`.
"""


# ------------------------------------------------------------ buggy and fixed
def add_item_buggy(item, order=[]):
    order.append(item)
    return order


def add_item(item, order=None):
    # TODO 1 (completed): new empty list when order is None
    if order is None:
        order = []
    order.append(item)
    return order


# -------------------------------------- alternative 1: caller passes the list
def add_item_explicit(item, order):
    order.append(item)
    return order


# -------------------------------- alternative 2: closure keeps one order each
def new_order():
    order = []                         # separate list for every customer

    def add(item):
        order.append(item)
        return order
    return add


# ------------------------------ positional / keyword / default parameters
PRICES = {"Tea": 12, "Vada": 10, "Dosa": 40, "Coffee": 15}


def bill(items, gst_rate=0.05, *, discount=0):
    """Return MORE THAN ONE value: (subtotal, gst, total) as a tuple."""
    subtotal = sum(PRICES[i] for i in items)
    gst = round(subtotal * gst_rate, 2)
    total = round(subtotal + gst - discount, 2)
    return subtotal, gst, total


# ------------------------------------------------ local / global / nonlocal
orders_served = 0                      # global name


def serve_wrong():
    # orders_served += 1  -> UnboundLocalError: assignment makes the name local
    pass


def serve_global():
    global orders_served               # needed because we REBIND a global name
    orders_served += 1


def make_counter():
    count = 0                          # enclosing (nonlocal) name

    def increment():
        nonlocal count                 # rebinds the enclosing variable
        count += 1
        return count
    return increment


if __name__ == "__main__":
    print("--- TODO 1 program ---")
    print(add_item_buggy("Tea"), add_item_buggy("Vada"))
    print(add_item("Tea"), add_item("Vada"))

    print("\n--- add_item_buggy.__defaults__ after the calls ---")
    print(add_item_buggy.__defaults__)
    print("It is the SAME list object that has grown: the default value was created "
          "once at 'def' time and every call without `order` appended to it.")

    print("\n--- Test: three customers in sequence, orders independent ---")
    c1 = add_item("Tea");   add_item("Vada", c1)
    c2 = add_item("Dosa");  add_item("Coffee", c2)
    c3 = add_item("Tea")
    print("customer 1:", c1)
    print("customer 2:", c2)
    print("customer 3:", c3)
    print("independent (different objects):", c1 is not c2 and c2 is not c3)

    print("\n--- closure design ---")
    cust_a, cust_b = new_order(), new_order()
    cust_a("Tea"); cust_a("Vada"); cust_b("Dosa")
    print("A:", cust_a("Coffee"), "| B:", cust_b("Tea"))

    print("\n--- explicit order design ---")
    mine = []
    add_item_explicit("Tea", mine); add_item_explicit("Dosa", mine)
    print(mine)

    print("\n--- positional, keyword and default parameters ---")
    print("positional      :", bill(["Tea", "Vada"]))
    print("keyword         :", bill(items=["Dosa"], gst_rate=0.12))
    print("default + kw-only:", bill(["Dosa", "Coffee"], discount=5))
    subtotal, gst, total = bill(["Tea", "Vada", "Dosa"])        # unpacking
    print(f"unpacked        : subtotal={subtotal} gst={gst} total={total}")

    print("\n--- local / global / nonlocal ---")
    try:
        def broken():
            orders_served += 1
        broken()
    except UnboundLocalError as e:
        print("without `global` ->", type(e).__name__ + ":", e)
    serve_global(); serve_global()
    print("with `global`, orders_served =", orders_served)
    inc = make_counter()
    print("nonlocal counter:", inc(), inc(), inc())

    local_demo = 5
    def shadow():
        local_demo = 99                # a NEW local, the outer one is untouched
        return local_demo
    print("shadowing: inside =", shadow(), "| outside =", local_demo)


"""
ANSWERS
Bug explanation (principle given): a default value is evaluated ONCE when the
`def` statement runs and stored in function.__defaults__. A list is mutable, so
append() changes that single stored object, and the next customer (a later call
without `order`) receives the same, already-filled list.

1. Positional vs keyword vs default parameters
   - Positional: required, obvious values whose order is natural (item, order).
   - Keyword: when there are several values or flags, for readability and to skip
     over defaults (bill(items=..., gst_rate=0.12)); keyword-only (after *)
     for options that must be named (discount=).
   - Default: for a sensible usual value (gst_rate=0.05). Use only IMMUTABLE
     defaults (numbers, strings, None); for a mutable one use None + create it
     inside.
2. Returning several values: return a tuple (return subtotal, gst, total) and
   unpack at the call (or return a dict / namedtuple when many values).
3. local = created by assignment inside a function, only there; global = module
   level, visible everywhere for reading; nonlocal = a name in an enclosing
   function, rebound from an inner function. (examples above)
4. Assignment inside a function makes the name LOCAL by default, so changing a
   module-level variable requires `global name`; otherwise Python raises
   UnboundLocalError (or creates a separate local). Globals are avoided
   because any function can change them, which makes bugs hard to trace,
   makes testing difficult and breaks re-use. Pass values in and return them out.

ALTERNATIVE CONCEPT (explicit list, closure, None default)
 - Time: O(1) per item (append is amortised O(1)) in every design.
 - Space per customer: O(m) for m items in each design, since each customer has
   exactly one list. Closure: one extra function object + cell per customer
   (O(1) overhead). None default: the list is allocated only when needed.
   Buggy default: ONE list of ALL customers' items (O(total items)) that never
   gets freed - a memory leak as well as a wrong result.
"""
