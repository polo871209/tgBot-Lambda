
# tgBot-Lambda

## tgBot intergration with AWS Lambda

**Goals to automate daily worklaods with serverless architecture**

### topology

![alt text](https://github.com/polo871209/tgBot-Lambda/blob/main/images/topology.png?raw=true)

### what I learn
  First of all, this is the first (python)project that I need to deploy different component. How to communicate between resource, permissions, API request, etc... Also, try to breakdown code using OOP.  
  I definitly learn that **no matter how hard this might think, there will be a solution eventually.**  
  Overall it's still an one man band, hopefully in the future I can become a developer and build big projects with others.


### RESULTS

### [Here](https://github.com/polo871209/tgBot-Lambda/blob/main/deploy.md) is how I deploy step by step on AWS.
### If you want to know how this code work, connect with me on [linkedIn](https://www.linkedin.com/in/potawian1998/).

#### Apply sectigo DV single/wildcard ssl

##### Now, we can simply apply SSL simply calling our bot, this will return CNAME value
![alt text](https://github.com/polo871209/tgBot-Lambda/blob/main/images/applyssl.png?raw=true)  

##### Add to your DNS record
```
;; ANSWER SECTION:
_36ac262b988daae06a577ce9f7df37e8.ilttats.com. 600 IN CNAME 6b2a48642ad4776f0d7ed6694469fd95.4018e519aeec89aeb880b7844a10b8d7.bwbazla0z6.sectigo.com
```
  
##### Domain Control Validation
![alt text](https://github.com/polo871209/tgBot-Lambda/blob/main/images/revalidate.png?raw=true)  
  
##### Check certificate status, expire date
**Once success, also show the expire date.**
![alt text](https://github.com/polo871209/tgBot-Lambda/blob/main/images/certstatus.png?raw=true)  
  
##### Download certifcate using presignurl
**This will zip all the files and generate pre-signedurl**  
![alt text](https://github.com/polo871209/tgBot-Lambda/blob/main/images/downloadcert.png?raw=true)  


##### Unzip will include all the certificate files

---

![alt text](https://github.com/polo871209/tgBot-Lambda/blob/main/images/result.png?raw=true)  

---

**Keen to add more functions in the future**