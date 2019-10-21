import camelot
import re
from io import StringIO
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from datetime import date

sellerRegex = {'đơn vị bán hàng|đơn vị bán': 'sellerLegalName', 'mã số thuế|mst': 'sellerTaxCode'}
buyerRegex = {'tên đơn vị|đơn vị': 'buyerLegalName', 'mã số thuế|mst': 'buyerTaxCode'}

################## GET DATES (CREATE DATE AND SIGNED DATE) #################

#converts pdf, returns its text content as a string
def convert(fname, pages=None):
    if not pages:
        pagenums = set()
    else:
        pagenums = set(pages)

    output = StringIO()
    manager = PDFResourceManager()
    converter = TextConverter(manager, output, laparams=LAParams())
    interpreter = PDFPageInterpreter(manager, converter)

    infile = open(fname, 'rb')
    for page in PDFPage.get_pages(infile, pagenums):
        interpreter.process_page(page)
    infile.close()
    converter.close()
    text = output.getvalue()
    output.close
    return text 

# split text to words by space and newline character
def preprocess(text):
    result = []
    
    # split to list of words
    result = text.split()
    
    return result

def checkLeapYear(year):  
    return (year%400==0)or(year%100!=0 and year%4==0)

# check date in form of 3 number day, month, year
def checkDate(day, month, year, minyear=1900, maxyear=2100):
    if not(minyear<=year<=maxyear):
        return False
    if month in [1, 3, 5, 7, 8, 10, 12]:
        if not(1<=day<=31):
            return False
    elif month in [4, 6, 9, 11]:
        if not(1<=day<=30):
            return False
    elif month in [2]:
        if not(1<=day<=28+checkLeapYear(year)):
            return False
    else:
        return False
    
    return True
    
# get 3 number day, month, year from date in form of string dd/mm/yyyy
def getDateFromString(datestring):
    result = datestring.replace('/', ' ').split()
    return int(result[0]), int(result[1]), int(result[2])
    
#check date in form of string dd/mm/yyyy
def checkDateString(datestring):
    day, month, year = getDateFromString(datestring)
    return checkDate(day, month, year)
    
#get the part from the title to above the part contains seller/buyer information(to get create date)
def getTop(text):
    result = ''
    begin = 0
    end = len(text)
    
    beginreg = ['hóa\s+đơn\s+giá\s+trị\s+gia\s+tăng']
    endreg = ['đơn vị bán hàng|đơn vị bán', 'mã số thuế|mst', 'địa chỉ', 'điện thoại', 'website', 'số tài khoản|stk']
    
    for reg in beginreg:
        found = re.search(reg, text, re.IGNORECASE)
        if found:
            begin = begin + found.start()
            break
    for reg in endreg:
        found = re.search(reg, text[begin:], re.IGNORECASE)
        if found:
            end = begin + found.start()
            break
            
    result = text[begin:end]
    return result

# get the part from the last cost found (to find signed date)
def getBot(text):
    result = ''
    begin = 0
    cost_regex = '\d{1,3}([.]\d{3})+'
    while True:
        found = re.search(cost_regex, text[begin:], re.IGNORECASE)
        if found:
            begin = begin + found.end()
        else:
            break
    result = text[begin:]
    return result

def getSignedDate(text):
    result = ''
    
    regex = '\d{2}\/\d{2}\/\d{4}'
    begin = 0
    while True:
        found = re.search(regex, text[begin:], re.IGNORECASE)
        if found:
            datestring = text[begin + found.start(): begin + found.end()]
            if checkDateString(datestring):
                result = datestring
            begin = begin + found.end()
        else:
            break
            
    return result

def getCreateDate(text):
    result = ''
    vector = preprocess(text)
    dayregex = '^(0?[1-9]|[12]\d|3[01])$'
    monthregex = '(0?[1-9]|1[012])$'
    yearregex = '^(19|20)\d{2}$'
    
    daylist = list(filter(re.compile(dayregex).match, vector))
    yearlist = list(filter(re.compile(yearregex).match, vector))
    if len(yearlist)>0:
        yearstring = yearlist[0]
        currentyear = date.today().year    
        for year in yearlist:
            if (int(year)<=currentyear and currentyear-int(year)<currentyear-int(yearstring)):
                yearstring = year
    else:
        return result
    
    if len(daylist)>=2 and len(yearlist):
        n = len(daylist)
        for i in range(n-1):
            for j in range(i+1, n):
                if re.match(monthregex, daylist[j]):
                    datestring = daylist[i] + '/' + daylist[j] + '/'+ yearstring
                    if checkDateString(datestring):
                        result = datestring
                        return result
                    
    return result

# get create date and signed date
def getAllDate(inputfile):
    text = convert(inputfile)
    
    result = {}
    createDate = ''
    signedDate = ''
    
    top = getTop(text)
    bot = getBot(text)
    
    createDate = getCreateDate(top)
    signedDate = getSignedDate(bot)
    
    result.update({'createDate': createDate})
    result.update({'signedDate': signedDate})
    return result

################# GET SELLER AND BUYER INFORMATION ######################

def preprocessTaxCode(code):
#     code = code.replace(' ', '')
#     code = code.replace('\n', '')
    result = ''
    for i in range(len(code)):
        if code[i] in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '-']:
            result = result + code[i]

    return result

#check if the cell contains basic info (tax code)
def containBasicInfo(cell):
    basicRegex = ['mã số thuế|mst']
    for reg in basicRegex:
        if not re.search(reg, cell, re.IGNORECASE):
            return False
    return True

#check if the cell contains buyer info
def containBuyerInfo(cell):
    buyerRegex = ['tên đơn vị|đơn vị', 'mã số thuế|mst', 'hình thức thanh toán|httt']
    for reg in buyerRegex:
        if not re.search(reg, cell, re.IGNORECASE):
            return False
    return True
    
#check if the cell contains seller info    
def containSellerInfo(cell):
    if containBasicInfo(cell) and not containBuyerInfo(cell):
        return True
    return False

#get seller name in the cell
def getSellerLegalName(cell):
    result = ''
    begin = 0
    end = len(cell)
    
    beginreg = ['đơn vị bán hàng|đơn vị bán']
    sellerreg = ['công ty', 'doanh nghiệp', 'tập đoàn']
    endreg = ['mã số thuế|mst', 'địa chỉ', 'điện thoại', 'website', 'số tài khoản|stk']
    
    for reg in beginreg:
        found = re.search(reg, cell[begin:], re.IGNORECASE)
        if found:
            begin = begin + found.end()
            colonfound = re.search(':', cell[begin:], re.IGNORECASE)
            if colonfound:
                begin = begin + colonfound.end()
            break
            
    for reg in endreg:
        found = re.search(reg, cell[begin:], re.IGNORECASE)
        if found:
            end = min(end, begin + found.start())
            
    for reg in sellerreg:
        found = re.search(reg, cell[begin:end], re.IGNORECASE)
        if found:
            begin = begin + found.start()
            break
            
    result = cell[begin:end]
    return result

#get seller info in the cell
def getSellerInfo(cell):
    result = {}
    allreg = ['đơn vị bán hàng|đơn vị bán', 'địa chỉ', 'mã số thuế|mst', 'điện thoại', 'website', 'số tài khoản|stk']
    for key, engkey in sellerRegex.items():
        if key == 'đơn vị bán hàng|đơn vị bán':
            value = getSellerLegalName(cell).strip()
            result.update({engkey:value})
        else:
            found = re.search(key, cell, re.IGNORECASE)
            if found:
                begin = found.end()
                firstcolonfound = re.search(':', cell[begin:], re.IGNORECASE)
                if firstcolonfound:
                    begin = begin + firstcolonfound.end()

                secondcolonfound = re.search(':', cell[begin:], re.IGNORECASE)
                end = len(cell)
                if secondcolonfound:
                    end = begin + secondcolonfound.end()

                for otherreg in allreg:
                    if not otherreg == key:
                        actualend = re.search(otherreg, cell[begin:end], re.IGNORECASE)
                        if actualend:
                            end = begin + actualend.start()
                            break
                        else:
                            end = end
                value = cell[begin : end].strip()
                if key == 'mã số thuế|mst':
                    value = preprocessTaxCode(value)
                result.update({engkey:value})
    return result
    
#get buyer info in the cell
def getBuyerInfo(cell):
    result = {}
    allreg = ['địa chỉ', 'mã số thuế|mst', 'điện thoại', 'website', 'họ tên người mua hàng|người mua', \
              'khách hàng', 'tên đơn vị|đơn vị', 'hình thức thanh toán|httt', 'số tài khoản|stk']
    for key, engkey in buyerRegex.items():
        found = re.search(key, cell, re.IGNORECASE)
        if found:
            begin = found.end()
            firstcolonfound = re.search(':', cell[begin:], re.IGNORECASE)
            if firstcolonfound:
                begin = begin + firstcolonfound.end()
            
            secondcolonfound = re.search(':', cell[begin:], re.IGNORECASE)
            end = len(cell)
            if secondcolonfound:
                end = begin + secondcolonfound.end()
        
            for otherreg in allreg:
                if not otherreg == key:
                    actualend = re.search(otherreg, cell[begin:end], re.IGNORECASE)
                    if actualend:
                        end = begin + actualend.start()
                        break
                    else:
                        end = end
            value = cell[begin : end].strip()
            if key == 'mã số thuế|mst':
                value = preprocessTaxCode(value)
            result.update({engkey:value})
    return result

################ GET COSTS #################

#check if the cell contain a cost number
def containCost(cell):
    cost_regex = '\d{1,3}([.]\d{3})+'
    if re.search(cost_regex, cell):
        return True
    return False

#get all cost in the cell
def getCosts(cell):
    cost_regex = '\d{1,3}([.]\d{3})+'
    
    result = []
    
    begin = 0
    while 1:
        found = re.search(cost_regex, cell[begin:])
        if found:
            result.append(cell[begin+found.start():begin+found.end()])
            begin = begin + found.end()
        else:
            break
    return result        
            
#get all cost in the tables    
def getAllCosts(tables):
    result = []
    
    for i in range(len(tables)):
        table = tables[i].df
        m, n = table.shape
        for i in range(m):
            row = table.iloc[i,:].values
            for j in range(n):
                cell = row[j]
                if containCost(cell):
                    result.extend(getCosts(cell))
    return result

#get totalWithoutVAT, totalVAT, and totalWithVAT
def getFinalCosts(allCosts):
    finalCosts = {'totalWithoutVAT': '', 'totalVAT': '', 'totalWithVAT': ''}
    if len(allCosts)<3:
        return finalCosts
    i = -3
    for reg in finalCosts.keys():
        finalCosts.update({reg: allCosts[i]})
        i += 1
    return finalCosts 

################ MAIN PROCESS #####################

# get information from table
def getPartiesInfo(tables):
    seller = {}
    buyer = {}
    
    for t in range(len(tables)):
        table = tables[t].df
        m, n = table.shape
        for i in range(m):
            row = table.iloc[i,:].values

            for j in range(n):
                cell = row[j]
                if len(seller)==0 and containSellerInfo(cell):
#                     print('seller: ', i, ', ', j)
                    seller = getSellerInfo(cell)
                elif len(buyer)==0 and containBuyerInfo(cell):
#                     print('buyer: ', i, ', ', j)
                    buyer = getBuyerInfo(cell)
                elif len(seller)>0 and len(buyer)>0:
                    return seller, buyer
     
    return seller, buyer

# get information from all tables                
def extract(inputfile):
    result = {}
    tables = camelot.read_pdf(inputfile, pages="1-end", flavor='lattice', process_background=True)
    
    date = {}   
    seller = {}
    buyer = {}
    finalCosts = {}
    allCosts = []
    
    allCosts = getAllCosts(tables)
    
    date = getAllDate(inputfile)
    finalCosts = getFinalCosts(allCosts)

    seller, buyer = getPartiesInfo(tables)    
        
    result.update(date)
    result.update(seller)
    result.update(buyer)
    result.update(finalCosts)
    
    return result