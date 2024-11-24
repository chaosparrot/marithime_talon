tag: browser
-
switch {user.website}: 
    browser.focus_address()
    insert(website)
    key(enter)