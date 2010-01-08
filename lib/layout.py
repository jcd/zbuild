import math

def table_layout(arr, header_line = False, prefix = "", do_sort = True):
    """
    return a string with a table layout of the [[]..]
    """
    sizes = []
    for i in arr:
        idx = 0
        for j in i:
            while True:
                try:
                    sizes[idx] = max(sizes[idx], len(str(j)))
                    break
                except:
                    sizes.append(0)
            idx += 1

    out = ""

    hl = None
    if header_line:
        hl = arr.pop(0)
    if do_sort:
        arr.sort(cmp=lambda a,b: cmp(a[0],b[0]))
    if hl:
        arr.insert(0,hl)
    for i in arr:
        idx = 0

        out += prefix
        for j in sizes:
            out += i[idx].ljust(j) 
            idx += 1
        out += "\n"

        if header_line:
            out += prefix
            for j in sizes:
                out += "-" * j
            out += "\n"
            header_line = False
    return out
    
def counter_length(arrlen):
        """
        Return number of digits to represent length of arr
        """
        if not arrlen:
                return 1
        return int(math.log10(arrlen)) + 1
