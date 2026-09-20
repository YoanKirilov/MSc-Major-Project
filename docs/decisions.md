# Implementation decisions

- Runtime persistence uses local UTF-8 JSON files only; no database or ORM is included.
- The current development environment is Windows with Python 3.14.2. The specification's reference environment is Ubuntu with Python 3.12, so live Linux route and Nmap checks remain pending.
- Nmap and OpenAI are optional at startup. Demo and offline model tests do not require either external prerequisite.
- The current repository contains an initial runnable scaffold and partial schema/storage/API implementation. Later tasks remain incomplete until their adapters and acceptance tests are implemented.
