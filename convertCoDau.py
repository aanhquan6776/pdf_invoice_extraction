def toLower(s):
    if type(s) == type(u""):
        return s.lower()
    return unicode(s, "utf8").lower().encode("utf8")

def preprocess(cell):
    result = []
    
    # remove unnecessary characters
    cell = cell.replace(',', '')
    cell = cell.replace('.', '')
    
    # convert to all lower case
    cell = toLower(cell)
    
    # split to list of words
    result = cell.split()
    
    return result

def convert(text):
    result = 0
    vector = preprocess(text)
    
    n = len(vector)
    
    post_dict = {'tỷ': 1000000000, 'triệu': 1000000, 'nghìn': 1000, 'trăm': 100, 'mươi': 10, 'đồng': 1}
    digit_dict = {'không': 0, 'một': 1, 'hai': 2, 'ba': 3, 'bốn': 4, 'tư': 4, 'năm': 5, 'lăm': 5, 'sáu': 6, 'bảy': 7, 'tám': 8, 'chín': 9, 'mười':10}
    
    stack = []
    
    l = 0
    
    for i in range(n):
        word = vector[i]
        if word in post_dict:
            val = post_dict.get(word)
            sum = 0
            while (stack) and (stack[-1] < val):
                sum += stack.pop()
            stack.append(sum*val)
        elif word in digit_dict:
            val = digit_dict.get(word)
            stack.append(digit_dict.get(word))          

    while stack:
        result += stack.pop()
    return result