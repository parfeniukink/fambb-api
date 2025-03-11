# ABOUT PROJECT

pet-project for LOGGING family FINANCIAL TRANSACTIONS

# GLOSSARY

| Item            | Description                                                                                                                                                                                                                                                                                                                       |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **FBB**         | stand for "Family Budget Bot". The name of a root project idea                                                                                                                                                                                                                                                                    |
| **Transaction** | from business model generalize next items: cost, income, exchange. So the transaction from the product perspective determines financial movement (_state change_). Since, that type of a 'transaction' meaning is just about logging real-life transactions - there is no reason to track the status of that particular data form |
| **Transaction** | from RDBMS is about technical operation that allows execute SQL queries with safe (could be wrapped into transaction and rolled back)                                                                                                                                                                                             |

# BACKLOG

- settings
  - number of 'Last Transactions' in 'Home'
  - accent color
  - hide equity (on home screen)
- authorization
  - if user credentials are not valid - return the WWW-Authorization HTTP header with detaild according to the RFC6750

# SETUP

```sh
uvicorn src.main:app --reload
uvicorn src.main:app --reload --loop uvloop
```
