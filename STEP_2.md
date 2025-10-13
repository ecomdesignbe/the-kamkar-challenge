# Step 1: Data Analysis

Now that we have the [HackerOne](https://hackerone.com/) program scopes, we need to clean them.

All scopes were written by hand, and there are many errors in how categories and entries were completed.
Sometimes a URL is written as a plain domain; sometimes a domain is written as a wildcard.
Sometimes domains are listed in [Punycode](https://fr.wikipedia.org/wiki/Punycode).
Sometimes domains have typos and are therefore invalid.
Sometimes domains are unresponsive.

The final task is to save the cleaned list of domains into a TXT file.

## Challenge

Write a Python script that contains three main functions: `extract_domains(programs_filename)`, `check_domains(domains_list)`, and `clean_domains()`.
You may add helper functions, but these three must be present.

### Function 1: `extract_domains`

This function takes a program filename as a parameter (for example: `"programs.json"`) and should return a list of domains.
The returned list must contain no duplicates. You should extract domains directly from the programs file.

This function must find all domains that are syntactically valid.

### Function 2: `check_domains`

This function takes a list of domains as a parameter and should return the list of active domains.
To determine if a domain is active, check whether it resolves to an IP address.

This function must find all the domains that are currently active.

### Function 3: `clean_domains`

This function uses the two previous functions to produce the final list of active domains from the programs file.
Use `extract_domains` to obtain all syntactically valid domains, then call `check_domains` to keep only the active ones. When finished, save the domain list to a text file.

## Expected Output File

The output file must be named `domains.txt`.
It should contain the list of active domains, one domain per line.
It should not contain duplicates.

Example:

```
tax.audible.com
www.mimeridian.com
www.centenepharmacy.com
...
```

**REMEMBER**: This file is required for the next step.

## Bonus

* `extract_domains`: Automatically fix domain syntax where possible.
* `extract_domains`: Find domains from wildcards by scanning for subdomains.
* `check_domains`: Use multithreading to speed up the scan.
