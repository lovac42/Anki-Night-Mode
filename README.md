# Night Mode for CCBC

This plugin adds a functionality of night mode, similar to the one implemented in AnkiDroid app.

### How it works?

It adds a "view" menu entity with options like:
- Automatic (i.e. at specified time) or manual switching of the night mode
- Inverting colors of images or latex formulas
- Defining custom color substitution rules

It provides shortcut <kbd>ctrl</kbd>+<kbd>n</kbd> to quickly switch mode and color picker to adjust some of color parameters.

After enabling the night mode, the add-on changes colors of menubar, toolbar, bottombars and content windows. Take a look at a screenshot at the bottom of this page to see an example.


#### Specifically replace a background of an element

given the HTML of your card:

```html
<div>Normal text <span style="background-color: rgb(240, 244, 198);">highlighted text</span></div>
```

```css
.night_mode span[style="background-color: rgb(240, 244, 198);"] {
    background-color: red!important;
}
```

#### Change the color of a cloze

```css
.night_mode .cloze {
    color: red!important;
}
```



## Screenshots:

<img src="https://github.com/lovac42/CCBC-Night-Mode/blob/master/screenshots/mainwindow.png?raw=true">  


<img src="https://github.com/lovac42/CCBC-Night-Mode/blob/master/screenshots/browser.png?raw=true">  

