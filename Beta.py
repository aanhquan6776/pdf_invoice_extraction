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
datespliter = ['-', '/']

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
    for spliter in datespliter:
        if re.search(spliter, datestring, re.IGNORECASE):
            result = datestring.replace(spliter, ' ').split()
            break
    return int(result[0]), int(result[1]), int(result[2])
    
#check date in form of string dd/mm/yyyy
def checkDateString(datestring):
    day, month, year = getDateFromString(datestring)
    return checkDate(day, month, year)
    
#get the part from the title to above the part contains seller/buyer information(to get create date)
def getCreateDatePart(text):
    result = ''
    begin = 0
    end = len(text)
    
    beginreg = ['ngày']
    endreg = ['năm']
    date_num_regex = '(19|20)\d{2}|([12]\d|3[01]|0?[1-9])'
    
    for reg in beginreg:
        found = re.search(reg, text, re.IGNORECASE)
        if found:
            begin = max(begin, found.start())
            
    for reg in endreg:
        found = re.search(reg, text[begin:], re.IGNORECASE)
        if found:
            end = min(end, begin + found.end())
            
    endfound = re.search(date_num_regex, text[end:], re.IGNORECASE)
    if endfound:
        end = end + endfound.end()
        
    result = text[begin:end]
    return result

def getSignedDatePart(text):
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

def getCreateDate(text):
    result = ''
    dayregex = '([12]\d|3[01]|0?[1-9])'
    monthregex = '(1[012]|0?[1-9])'
    yearregex = '(19|20)\d{2}'
    daylist = []
    yearlist = []
    
    begin = 0
    end = len(text)

    while begin<end:
        found = re.search(yearregex, text[begin:], re.IGNORECASE)
        if found:
            yearlist.append(text[begin+found.start(): begin+found.end()])
            text = text.replace(text[begin+found.start(): begin+found.end()], '    ', 1)
            begin = begin + found.end()
        else:
            break
    begin = 0       
    while begin<end:
        found = re.search(dayregex, text[begin:], re.IGNORECASE)
        if found:
            daylist.append(text[begin+found.start(): begin+found.end()])
            begin = begin + found.end()
        else:
            break
    
    
#     print(daylist)
#     print(yearlist)
#     if len(yearlist)>0:
#         yearstring = yearlist[0]
#         currentyear = date.today().year    
#         for year in yearlist:
#             if (int(year)<=currentyear and currentyear-int(year)<currentyear-int(yearstring)):
#                 yearstring = year
#     else:
#         return result
    
    if yearlist:
        yearstring = yearlist[0]
        if len(daylist)>=2:
            n = len(daylist)
            for i in range(n-1):
                for j in range(i+1, n):
                    if re.match(monthregex, daylist[j]):
                        datestring = daylist[i] + '/' + daylist[j] + '/'+ yearstring
                        if checkDateString(datestring):
                            result = datestring
                            return result
        elif len(daylist)>0:
            if re.match(monthregex, daylist[0]):
                datestring = '1' + '/' + daylist[0] + '/'+ yearstring
                if checkDateString(datestring):
                    result = datestring
                    return result
    return result

def getSignedDate(text):
    result = ''
    
    regex = '\d{1,2}[\/|-]\d{1,2}[\/|-]\d{4}'
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

# get create date and signed date
def getAllDate(text):
    result = {}
    createDate = ''
    signedDate = ''
    
    createDatePart = getCreateDatePart(text)
    signedDatePart = getSignedDatePart(text)
    
    createDate = getCreateDate(createDatePart)
    signedDate = getSignedDate(signedDatePart)
    
    result.update({'createDate': createDate})
    result.update({'signedDate': signedDate})
    return result

################# GET SELLER INFORMATION ######################
def preprocessLegalName(name):
    return ' '.join(name.split())

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
#     print(cell)  
    result = ''
    begin = 0
    end = len(cell)
    
    beginreg = ['đơn vị bán hàng|đơn vị bán']
    sellerreg = ['công ty', 'doanh nghiệp', 'tập đoàn', 'chi nhánh', 'tổng công ty']
    endreg = ['mã số thuế|mst', 'địa chỉ', 'điện thoại', 'website', 'số tài khoản|stk']
    otherreg = ['hóa đơn', 'giá trị', 'gia tăng', 'mẫu số', 'ký hiệu', 'số', 'liên', 'ngày', 'tháng', 'năm']
    
    for reg in beginreg:
        found = re.search(reg, cell[begin:], re.IGNORECASE)
        if found:
            begin = begin + found.end()
            colonfound = re.search(':', cell[begin:], re.IGNORECASE)
            if colonfound:
                begin = begin + colonfound.end()
            break
    
    tmp = end
    for reg in sellerreg:
        found = re.search(reg, cell[begin:end], re.IGNORECASE)
        if found:
            tmp = min(tmp, found.start())
    if tmp==end:
        begin = begin
    else:
        begin = begin + tmp

    for reg in endreg:
        found = re.search(reg, cell[begin:], re.IGNORECASE)
        if found:
            end = min(end, begin + found.start())
    
    for reg in otherreg:
        found = re.search(reg, cell[begin:], re.IGNORECASE)
        if found:
            end = min(end, begin + found.start())
            
    result = cell[begin:end].strip()
    return result

#get seller info in getSellerInfo function fail
def backupSellerInfo(text, seller):
    for key, engkey in sellerRegex.items():
        if len(seller.get(engkey))==0:
            return getSellerInfo(text)
    return seller

#get seller info in the cell
def getSellerInfo(cell):
    result = {}
    basic_regex = 'mã số thuế|mst'
    seller_regex = 'đơn vị bán hàng|đơn vị bán'
    buyer_regex = 'khách hàng|mua hàng|tên đơn vị|đơn vị'
    third_regex = 'cung cấp giải pháp hóa đơn điện tử|phát hành|bởi'
    all_regex = ['địa chỉ', 'mã số thuế|mst', 'điện thoại', 'website', 'số tài khoản|stk']
    
    start = 0
        
    while start<len(cell):
        # firstly, search for taxcode in the text
        taxcode_found = re.search(basic_regex, cell[start:], re.IGNORECASE)
        if taxcode_found:
            # ensure that it is seller information          
            if re.search(seller_regex, cell[start: start + taxcode_found.start()], re.IGNORECASE) \
            or (not re.search(buyer_regex, cell[start: start + taxcode_found.start()], re.IGNORECASE) \
            and not re.search(third_regex, cell[start: start + taxcode_found.start()], re.IGNORECASE)):
                # get the name and the taxcode
                for key, engkey in sellerRegex.items():
                    if key == seller_regex:
                        value = preprocessLegalName(getSellerLegalName(cell[start:start+taxcode_found.start()]))
                        result.update({engkey:value})
                    else:
                        begin = start + taxcode_found.end()
                        firstcolonfound = re.search(':', cell[begin:], re.IGNORECASE)
                        if firstcolonfound:
                            begin = begin + firstcolonfound.end()

                        secondcolonfound = re.search(':', cell[begin:], re.IGNORECASE)
                        end = len(cell)
                        if secondcolonfound:
                            end = begin + secondcolonfound.end()

                        for otherreg in all_regex:
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
            else:
                start = taxcode_found.end()
        else:
            break
            
    return result

################ GET COSTS #################

#check if the cell contain a cost number
def containCost(cell):
    cost_regex = '\d{1,3}([.]\d{3})+([,]\d+)?'
    if re.search(cost_regex, cell):
        return True
    return False

#get all cost in the cell
def getCosts(cell):
    cost_regex = '\d{1,3}([.]\d{3})+([,]\d+)?'
    
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
#                 elif len(buyer)==0 and containBuyerInfo(cell):
# #                     print('buyer: ', i, ', ', j)
#                     buyer = getBuyerInfo(cell)
                elif len(seller)>0 and len(buyer)>0:
                    return seller, buyer
     
    return seller, buyer

# get information from all tables                
def extract_from_pdf(inputfile):
    result = {}
    tables = camelot.read_pdf(inputfile, pages="1-end", flavor='lattice', process_background=True)
    text = convert(inputfile)
    
    date = {}   
    seller = {}
#     buyer = {}
    finalCosts = {}
    allCosts = []
    
    allCosts = getAllCosts(tables)
    
    date = getAllDate(text)
    finalCosts = getFinalCosts(allCosts)

    seller, buyer = getPartiesInfo(tables)    
        
    result.update(date)
    
    if len(seller)==0:
        seller = {'sellerLegalName': '', 'sellerTaxCode': ''}
    seller = backupSellerInfo(text, seller)
    
#     if len(buyer)==0:
#         buyer = {'buyerLegalName': '', 'buyerTaxCode': ''}
    
    
    result.update(seller)
#     result.update(buyer)
    result.update(finalCosts)
    
    return result