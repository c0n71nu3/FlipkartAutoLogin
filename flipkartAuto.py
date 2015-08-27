# flipkart login 

import urllib, urllib2
import cookielib
import sys
from bs4 import BeautifulSoup

class WebLogin(object):
  def __init__(self, username, password):
    # url for website we want to log in to
    self.base_url = "https://www.flipkart.com";
    self.loginUrl = self.base_url + "/account/loginWithoutOtp";

    # to be able to access an internal URL, as per my observation, a call gets made to /xhr/getNotifications supplying __FK as the query parameter.
    # accessing the above sets a cookie (can be seen in the response), by the name SN, something like 
    # SN=2.VI28B194AC3B97475DB05CA360A3C58A82.SIE67A93CFA67E437AAB0CF1C69690CDD0.VS143359826787245684834.1433600020
    # (the right most value in the above actually keeps changing for every call to /xhr/getNotifications)
    # after the SN cookie is set post the /xhr/getNotifications call, the next URL can be accessed. 

    self.SNCookieFetchUrl = "/xhr/getNotifications?";
    self.internalUrl = "/account/addresses";
    
    
    # user supplied username and password
    self.username = username;
    self.password = password;

    # file for storing cookies
    self.cookie_file = 'login.cookies'

    # set up a cookie jar to store cookies
    self.cj = cookielib.MozillaCookieJar(self.cookie_file);
    # set up opener to handle cookies, redirects etc
    self.opener = urllib2.build_opener(
      urllib2.HTTPRedirectHandler(),
      urllib2.HTTPHandler(debuglevel=0),
      urllib2.HTTPSHandler(debuglevel=0),
      urllib2.HTTPCookieProcessor(self.cj)
    );
    
    # open the front page of the website to set and save initial cookies and to retrieve the csrf token (__FK is the csrf token here) required for login
    response = self.opener.open(self.base_url);
    self.cj.save();
    if (response):
      self.initialResponse = response.read();
      #print "\nResponse received for \n\n",self.initialResponse;
    
    self.csrfToken = self.csrfTokenParser();

    # trying to login
    self.opener.addheaders = [
        ('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:37.0) Gecko/20100101 Firefox/37.0'),
        #('Referer', 'https://www.flipkart.com/'),
        ('Connection', 'keep-alive'),
        ('Pragma', 'no-cache'),
        ('Cache-Control', 'no-cache'),
        #('Accept','text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
        #('Accept-Encoding','gzip,deflate'),
        #('Accept-Language', 'en-US,en;q=0.5'),
        ];
    # set up a cookie jar to store cookies
    self.cj.save();

    loginResponse = self.login();
    if(loginResponse):
      
      # Checking for a succesful login
      print "\n\nSTSUS CODE FOUND  ",loginResponse.getcode();
      if(loginResponse.getcode() == 200):
        loginResponseBody = loginResponse.read();
        successFullLogin = loginResponseBody.find("VERIFIED");
        if(successFullLogin > -1 ):
          print "\n\nLogged in succesfully";
          print "\n\nResponse Body is \n\n",loginResponseBody;

          # making another call to www.flipkart.com to retrieve the __FK csrftoken post successful login
          response = self.opener.open("https://www.flipkart.com/");
          if (response):
            #print "\n\nSuccessfully recevived the response page with the new __FK token post successful login";
            self.initialResponse = response.read();
            self.csrfToken = self.csrfTokenParser();
            #print "\n\n the new CSRF token is ",self.csrfToken;
          else :
            print "\n\ncould not retrieve the response for an internal page post login !!";
          # now we have the new __FK csrfToken post login

          # fetching the SN cookie by navigating to the URL /xhr/getNotifications?__FK= defined by self.SNCookieFetchUrl
          encodedCSRFToken = urllib.urlencode({'__FK':self.csrfToken});
          #print "\n\n Fetching the SN cookie...";
          self.navigateToUrl = self.base_url + self.SNCookieFetchUrl + encodedCSRFToken;
          #self.navigateToUrl = urllib.quote(self.csrfToken);
          #print "\n\n The SN Cookie URL is ",self.navigateToUrl;
          navigationResponse = self.navigateTo();
          if(navigationResponse):
            navigationResponseBody = navigationResponse.read();
            print "\n\nResponse receviced after hitting the SN token URL\n\n",navigationResponseBody;
          
          # Navigating to an internal URL -> defined by self.internalUrl. 
          self.cj.save();
          self.navigateToUrl = self.base_url + self.internalUrl;
          navigationResponse = self.navigateTo();
          if(navigationResponse):
            navigationResponseBody = navigationResponse.read();
            #print "\n\n\nResponse received after navigation is  \n\n\n",navigationResponseBody;
            #if(navigationResponseBody.find("GENDER") or navigationResponseBody.find("gender")):
            #if(navigationResponseBody.find("9123456789")):
            soup = BeautifulSoup(navigationResponseBody);
            if(soup):
              #print "\n\n\n\nPrinting the soup !!\n\n\n";
              #print soup;
              #if(navigationResponseBody.find("address_ADD14334352618381633") > -1):
                #print "\n\nFetching the address with the address id address_ADD14334352618381633";
              myAddress = soup.findAll("input",attrs={'id':'default_billing_address'});
              addressIdHolder = myAddress[0]['onclick'];
              addressId = "address_"+addressIdHolder[19:-2];
              print "\n\nthe address id is ",addressId;
              print "\n\nprinting the value of myAddress\n\n ",addressId;
              print "\n\n\nThe current URL is  ",navigationResponse.geturl();
              myAddress = soup.find("div",attrs={'id':addressId});
              if(myAddress):
                print "\n\n succesfully retrieved the internal page !! ";
                print "\n\n My address is \n\n",myAddress.text;
                #print "\n\n\nIN YOUR FACE BITCH !!\n\n\n ";
              else:
                print"\n\n\n couldn't retrieve the internal page :( "; 
            else:
              print "\n\n\n There was some error making the soup !!";

  
  # the method extracts CSRF tokens from response pages
  def csrfTokenParser(self):
    #print "\n\ninside the csrfTokenParser method "
    # parsing the response for csrf token
    csrfTokenStartIndex = self.initialResponse.find("window.__FK");
    if (csrfTokenStartIndex > -1):
      #print"\n first instance of window.__FK FOUND at index ",csrfTokenStartIndex;
      csrfTokenEndIndex = self.initialResponse.find("window.__FK", csrfTokenStartIndex+1);
      if (csrfTokenEndIndex > -1):
        #print"\n second instance of window.__FK found at index",csrfTokenEndIndex;
        # finding the first occurrence of ; between the csrfTokenStartIndex and csrfTokenEndIndex
        semiColonTokenIndex = self.initialResponse.find(";",csrfTokenStartIndex,csrfTokenEndIndex);
        if (semiColonTokenIndex > -1):
          #print "\n semiColonToken found at index ",semiColonTokenIndex;
          csrfToken = self.initialResponse[csrfTokenStartIndex+15:semiColonTokenIndex-1];
          csrfToken = csrfToken + "=";
          #print csrfToken;
          return csrfToken;
  

  # method to navigate to an internal URL 
  def navigateTo(self):
    #print "\n\nnavigating to an internal URL now...\n\n";
    response = self.opener.open(self.navigateToUrl);
    return response;

  # method to do login
  def login(self):
  # parameters for login action
  # may be different for different websites
  # check html source of website for specifics
    #print "\n\n\ninside the login method\n\n"
    #self.cj.save();
    login_data = urllib.urlencode({
      '__FK' : self.csrfToken,
      'contact_id' : self.username,
      'password' : self.password,
    });
    print "\nlogin URL "+self.loginUrl;
    #self.cj = cookielib.MozillaCookieJar(self.cookie_file);
    #self.cj.save();
    # then open it
    response = self.opener.open(self.loginUrl, login_data)
    # save the cookies and return the response
    self.cj.save();
    #print "\n\nresponse inside login method",response.read();
    return response;

# calling the main method. 
if __name__ == "__main__":
  args = sys.argv;
  # check for username and password
  if len(args) != 3:
    print "Incorrect number of arguments";
    print "Argument pattern: username password";
    exit(1);
  username = args[1];
  password = args[2];
  
  # print out some initial messages 
  print "\nThe script has been tested from within the corporate network to avoid captcha or any other RL";
  print "\nPlease make sure you have the following py modules installed for running the script succesfully\nBeautifulSoup\njson2html\nordereddict\ngzip\nurlib and urllib2.";
  print "\nAnother file that gets created in your current directory is login.cookies which is used to manage the logged in sessions. Please do NOT erase it UNLESS";
  print "compulsarily only when the script is run again";
  # initialise and login to the website
  WebLogin(username, password);