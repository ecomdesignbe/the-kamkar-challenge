# Step 1: Web Scraping

[HackerOne](https://hackerone.com/) is a bug-bounty platform.
By browsing the [directory](https://hackerone.com/directory/programs) you can see the list of all available programs.
Each program has a strict scope, a scope is the list of targets where you may try to find vulnerabilities (examples: [Netflix scope](https://hackerone.com/netflix/policy_scopes), [Reddit scope](https://hackerone.com/reddit/policy_scopes), ...).

The first task is to save the list of all program scopes from HackerOne into a JSON file.


## Challenge
Write a Python script that contains three main functions: `get_scope(program_handle)`, `get_programs_list()`, and `scrape_hackerone()`.
You may add additional helper functions, but these three must be present.

### Function 1: `get_scope`
This function takes a program handle as a parameter (for example: `"canada_goose_inc"`, `"dyson"`, ...) and should return the program’s [scope](https://hackerone.com/netflix/policy_scopes) as a dictionary.
The returned dictionary may include up to three different lists: **domains**, **urls**, and **wildcards**.
Ignore other target categories (smart contracts, software, mobile apps, etc.).

Usage:
```python
print(get_scope("audible"))

# EXPECTED OUTPUT: {'domains': ['tax.audible.com']}
```

### Function 2: `get_programs_list`
This function should return the list of all program handles scraped from the HackerOne [directory page](https://hackerone.com/directory/programs).
Warning: return only the handles, not the scopes.

Usage:
```python
print(get_programs_list())

# EXPECTED OUTPUT: ['audible', 'alibaba_vdp', 'centene_vdp', ...]
```

### Function 3: `scrap_hackerone`
This function uses the two previous functions to scrape all program scopes.
Use `get_programs_list` to list programs handles, call `get_scope` for each handle, then save the aggregated results to a JSON file.


## Expected Output File

The output file must be named `programs.json`.
It should contain the domains, URLs, and wildcards for each program.

The JSON must follow the format in this example:
```json
{
    "audible": {
        "domains": [
            "tax.audible.com"
        ]
    },
    "alibaba_vdp": {
        "wildcards": [
            "www.lazada.*sixcountry",
            "*.youku.com"
        ]
    },
    "centene_vdp": {
        "domains": [
            "www.mimeridian.com"
        ],
        "wildcards": [
            "*.ambetterhealth.com"
        ],
        "urls": [
            "https://www.centenepharmacy.com"
        ]
    }
}
```

REMEMBER: This file is required for the next step.


## Bonus
- get_scope: Only save targets marked **In Scope**.
- get_scope: Only save targets marked **Eligible**.
- scrap_hackerone: Add multithreading to speed up scraping.
- Add support for other bug-bounty platforms.