import base64
import requests
from bs4 import BeautifulSoup

#第一步，登录SSRN
keywords="填你要搜索的信息"
username="填你的用户名"
password="填你的密码"
remember="0"
key=username+"|"+password+"|"+remember
keyUser=base64.b64encode(key.encode())
strForwardURL = "https://hq.ssrn.com/UserHome.cfm"
parameters = {
            "key": keyUser,
            "strForwardURL": strForwardURL
        	}
loginUrl = "https://hq.ssrn.com/login/cfc/hqLoginServices.cfc?method=signinService";
strHqServer = "https://hq.ssrn.com"
headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.2) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.12 Safari/535.11'}
ss=requests.Session()
r = ss.post(loginUrl, data=parameters, headers=headers)
print(r.status_code)
#c=r.cookies
#u = requests.get("https://hq.ssrn.com/UserHome.cfm",cookies=c,headers=headers)

#第二步爬取paper信息
search={"txtKey_Words":keywords, "isQuickSearch": "true"}
searchUrl="https://papers.ssrn.com/sol3/results.cfm"
papers = ss.post(searchUrl,data=search,headers=headers)
soup=BeautifulSoup(papers.content, 'lxml')
paper_list = soup.find_all(attrs={"class":"title optClickTitle"})

#如果搜索的内容没有，则返回一段话，否则提取信息
if not paper_list:
    print("no result for your keywords")
else:
    first_Url=paper_list[0]['href']
    first_paper = ss.get(first_Url, headers=headers,verify=False)
    soup_p=BeautifulSoup(first_paper.content, 'lxml')
    info=soup_p.find_all(attrs={"class":"box-container box-abstract-main"})

    #info包含文章所有信息，提取所有作者以及他们的affiliation，还有年份
    title = info[0].h1.get_text()
    authors = info[0].find_all(attrs={"class":"authors authors-full-width"})
    name=authors[0].find_all(name="h2")
    association=authors[0].find_all(name="p")
    name_list=[]
    association_list=[]
    for i in range(len(name)):
        name_list.append(name[i].string)
        association_list.append(association[i].string)
    date_0 = soup_p.find_all(attrs={"class":"note note-list"})
    date_1 = date_0[0].find_all(name="span")
    date_2 = date_1[1].string
    year = date_2.split()[-1]

    #分析文章标题，生成latex引用的shortcut，如果开头是定冠词，则选第二个词
    if title.split(' ')[0]=='The' or title.split(' ')[0]=='A' or title.split(' ')[0]=='An':
        short=title.split(' ')[1]
    else:
        short=title.split(' ')[0]
    short_title = name_list[0].split(' ')[-1].lower()+year+short.lower()
    
    #提取作者的姓和名，做成文献引用模板
    authors_l=[]
    for x in name_list:
        surname= x.split(' ')[-1]
        givenname=''
        for y in range(len(x.split(' '))-1):
            givenname = givenname + x.split(' ')[y][0]
        authors_l.append(surname+", "+givenname)
    a_bib = authors_l[0]
    if len(authors_l)!=1:
        for k in range(1,len(authors_l)):
            a_bib=a_bib+' and '+authors_l[k]
    
    #提取参考文献中的文章链接   
    h = info[0].find_all(attrs={"class":"suggested-citation"})   
    h0=h[0].find_all(attrs={"class":"textlink"})
    if h0:
        h_bib =h0[0]['href'] 
    else:
        h_bib=h[0].find_all(name="a")[0]['href']
    
    #生成bib需要的引用文本
    bib=r"@unpublished{"+short_title+r","+"\n"+\
    r"  title={"+title+r"},"+"\n"+\
    r"  author={"+a_bib+r"},"+"\n"+\
    r"  year={"+year+r"},"+"\n"+\
    r"  note={\url{"+h_bib+r"}}"+"\n"+\
    r"}"
    bibname = name_list[0]+" "+ year+" "+"SSRN"+".txt"
    with open(bibname, 'w', encoding="UTF-8") as file_object:
        file_object.write(bib)
    
    #下载pdf文件
    download = soup_p.find_all(attrs={"class":"button-link primary"})
    DU="https://papers.ssrn.com/sol3/"+download[0]["href"]
    header = {'referer':first_paper.url,
              'upgrade-Insecure-Requests': '1',
              'user-agent':'Mozilla/5.0 (Windows NT 6.2) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.12 Safari/535.11'}
    d_r=ss.get(DU, headers=header,allow_redirects=False)
    print(d_r.status_code)
    final=ss.get(d_r.headers['Location'],headers=header)
    file_name=name_list[0]+" "+ year+" "+"SSRN"+".pdf"
    with open(file_name,"wb") as f:
        f.write(final.content) 