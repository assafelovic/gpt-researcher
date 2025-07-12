# Showdown Options

[Jump to bottom](https://github.com/showdownjs/showdown/wiki/Showdown-options#wiki-pages-box)

Estevão Soares dos Santos edited this page Dec 3, 2017
·
[8 revisions](https://github.com/showdownjs/showdown/wiki/Showdown-Options/_history)

## Setting options

[Permalink: Setting options](https://github.com/showdownjs/showdown/wiki/Showdown-options#setting-options)

Options can be set:

### Globally

[Permalink: Globally](https://github.com/showdownjs/showdown/wiki/Showdown-options#globally)

Setting a "global" option affects all instances of showdown

```js
showdown.setOption('optionKey', 'value');
```

### Locally

[Permalink: Locally](https://github.com/showdownjs/showdown/wiki/Showdown-options#locally)

Setting a "local" option only affects the specified Converter object.
Local options can be set:

- **through the constructor**

```js
var converter = new showdown.Converter({optionKey: 'value'});
// example of multiple options
var converter = new showdown.Converter({tables: true, strikethrough: true});
```

- **through the setOption() method**

```js
var converter = new showdown.Converter();
converter.setOption('optionKey', 'value');
```

## Getting an option

[Permalink: Getting an option](https://github.com/showdownjs/showdown/wiki/Showdown-options#getting-an-option)

Showdown provides 2 methods (both local and global) to retrieve previous set options.

### getOption()

[Permalink: getOption()](https://github.com/showdownjs/showdown/wiki/Showdown-options#getoption)

```js
// Global
var myOption = showdown.getOption('optionKey');

//Local
var myOption = converter.getOption('optionKey');
```

### getOptions()

[Permalink: getOptions()](https://github.com/showdownjs/showdown/wiki/Showdown-options#getoptions)

```js
// Global
var showdownGlobalOptions = showdown.getOptions();

//Local
var thisConverterSpecificOptions = converter.getOptions();
```

#### Retrieve the default options

[Permalink: Retrieve the default options](https://github.com/showdownjs/showdown/wiki/Showdown-options#retrieve-the-default-options)

You can get showdown's default options with:

```js
var defaultOptions = showdown.getDefaultOptions();
```

## Valid Options

[Permalink: Valid Options](https://github.com/showdownjs/showdown/wiki/Showdown-options#valid-options)

Please note that until version 1.6.0, all of these options are _**DISABLED**_ by default in the cli tool.

### omitExtraWLInCodeBlocks

[Permalink: omitExtraWLInCodeBlocks](https://github.com/showdownjs/showdown/wiki/Showdown-options#omitextrawlincodeblocks)

| type | default | since | description |
| :-: | :-: | :-: | :-- |
| boolean | false | 1.0.0 | Omit the trailing newline in a code block |

By default, showdown adds a newline before the closing tags in code blocks. By enabling this option, that newline is removed.

This option affects both indented and fenced (gfm style) code blocks.

#### Example

[Permalink: Example:](https://github.com/showdownjs/showdown/wiki/Showdown-options#example)

**input**:

```js
    var foo = 'bar';
```

**omitExtraWLInCodeBlocks** = false:

```html
<code><pre>var foo = 'bar';
</pre></code>
```

**omitExtraWLInCodeBlocks** = true:

```html
<code><pre>var foo = 'bar';</pre></code>
```

### noHeaderId

[Permalink: noHeaderId](https://github.com/showdownjs/showdown/wiki/Showdown-options#noheaderid)

| type | default | since | description |
| :-: | :-: | :-: | :-- |
| boolean | false | 1.1.0 | Disable the automatic generation of header ids |

Showdown generates an id for headings automatically. This is useful for linking to a specific header.
This behavior, however, can be disabled with this option.

#### Example

[Permalink: Example](https://github.com/showdownjs/showdown/wiki/Showdown-options#example-1)

**input**:

```js
# This is a header
```

**noHeaderId** = false

```html
<h1 id="thisisaheader">This is a header</h1>
```

**noHeaderId** = true

```html
<h1>This is a header</h1>
```

NOTE: Setting to true overrides **[prefixHeaderId](https://github.com/showdownjs/showdown/wiki/Showdown-options#prefixheaderid)** and **[ghCompatibleHeaderId](https://github.com/showdownjs/showdown/wiki/Showdown-options#ghcompatibleheaderid)** options

### ghCompatibleHeaderId

[Permalink: ghCompatibleHeaderId](https://github.com/showdownjs/showdown/wiki/Showdown-options#ghcompatibleheaderid)

| type | default | since | description |
| :-: | :-: | :-: | :-- |
| boolean | false | 1.5.5 | Generate header ids compatible with github style |

This changes the format of the generated header IDs: spaces are replaced with dashes and a bunch of non alphanumeric chars are removed.

#### Example

[Permalink: Example](https://github.com/showdownjs/showdown/wiki/Showdown-options#example-2)

**input**:

```html
# This is a header with @#$%
```

**ghCompatibleHeaderId** = false

```html
<h1 id="thisisaheader">This is a header</h1>
```

**ghCompatibleHeaderId** = true

```html
<h1 id="this-is-a-header-with-">This is a header with @#$%</h1>
```

### prefixHeaderId

[Permalink: prefixHeaderId](https://github.com/showdownjs/showdown/wiki/Showdown-options#prefixheaderid)

| type | default | since | description |
| :-: | :-: | :-: | :-- |
| string \| boolean |  | 1.0.0 | Add a prefix to the generated header ids |

Adds a prefix to the generated header ids. Passing a string will prefix that string to the header id. Setting to `true` will add a generic 'section' prefix.

### headerLevelStart

[Permalink: headerLevelStart](https://github.com/showdownjs/showdown/wiki/Showdown-options#headerlevelstart)

| type | default | since | description |
| :-: | :-: | :-: | :-- |
| integer | 1 | 1.1.0 | Set the header starting level |

Sets the level from which header tags should start

**input**:

```html
# header
```

**headerLevelStart** = 1

```html
<h1>header</h1>
```

**headerLevelStart** = 3

```html
<h3>header</h3>
```

### parseImgDimensions

[Permalink: parseImgDimensions](https://github.com/showdownjs/showdown/wiki/Showdown-options#parseimgdimensions)

| type | default | since | description |
| :-: | :-: | :-: | :-- |
| boolean | false | 1.1.0 | Enable support for setting image dimensions from within markdown syntax |

Enables support for setting image dimensions from within markdown syntax.

```js
![foo](foo.jpg =100x80)   simple, assumes units are in px
![bar](bar.jpg =100x*)    sets the height to "auto"
![baz](baz.jpg =80%x5em)  Image with width of 80% and height of 5em

```

#### simplifiedAutoLink

[Permalink: simplifiedAutoLink](https://github.com/showdownjs/showdown/wiki/Showdown-options#simplifiedautolink)

| type | default | since | description |
| :-: | :-: | :-: | :-- |
| boolean | false | 1.2.0 | Enable automatic linking in plain text urls |

Turning this option on will enable automatic linking when the parser find plain text urls

**input**:

```js
some text www.google.com
```

**simplifiedAutoLink** = false

```html
<p>some text www.google.com</p>
```

**simplifiedAutoLink** = true

```html
<p>some text <a href="www.google.com">www.google.com</a></p>
```

### excludeTrailingPunctuationFromURLs

[Permalink: excludeTrailingPunctuationFromURLs](https://github.com/showdownjs/showdown/wiki/Showdown-options#excludetrailingpunctuationfromurls)

| type | default | since | description |
| :-: | :-: | :-: | :-- |
| boolean | false | 1.5.1 | Excludes trailing punctuation from autolinked urls |

Excludes the follow characters from links: `. !  ? ( )`
This option only applies to links generated by **[simplifiedAutoLink](https://github.com/showdownjs/showdown/wiki/Showdown-options#simplifiedautolink)**.

**input**:

```html
   check this link www.google.com.
```

**excludeTrailingPunctuationFromURLs** = false

```html
<p>check this link <a href="www.google.com">www.google.com.</a></p>
```

**excludeTrailingPunctuationFromURLs** = true

```html
<p>check this link <a href="www.google.com">www.google.com</a>.</p>
```

### literalMidWordUnderscores

[Permalink: literalMidWordUnderscores](https://github.com/showdownjs/showdown/wiki/Showdown-options#literalmidwordunderscores)

| type | default | since | description |
| :-: | :-: | :-: | :-- |
| boolean | false | 1.2.0 | Treats underscores in middle of words as literal characters |

Underscores are _magic characters_ in markdown (as they delimit words that should be emphasised).
Turning this on will stop showdown from interpreting underscores in the middle of words as `<em>` and `<strong>` and instead treat them as literal underscores.

**input**:

```html
some text with__underscores__in middle
```

**literalMidWordUnderscores** = false

```html
<p>some text with<strong>underscores</strong>in middle</p>
```

**literalMidWordUnderscores** = true

```html
<p>some text with__underscores__in middle</p>
```

### strikethrough

[Permalink: strikethrough](https://github.com/showdownjs/showdown/wiki/Showdown-options#strikethrough)

| type | default | since | description |
| :-: | :-: | :-: | :-- |
| boolean | false | 1.2.0 | Enable support for strikethrough syntax |

Enables support for strikethrough ( `<del>`)

**syntax**:

```html
~~strikethrough~~
```

```html
<del>strikethrough</del>
```

### tables

[Permalink: tables](https://github.com/showdownjs/showdown/wiki/Showdown-options#tables)

| type | default | since | description |
| :-: | :-: | :-: | :-- |
| boolean | false | 1.2.0 | Enable support for tables syntax |

Enables support for table syntax.

**syntax**:

```md
| h1    |    h2   |      h3 |
|:------|:-------:|--------:|
| 100   | [a][1]  | ![b][2] |
| *foo* | **bar** | ~~baz~~ |
```

#### tablesHeaderId\*\*

[Permalink: tablesHeaderId**:](https://github.com/showdownjs/showdown/wiki/Showdown-options#tablesheaderid)

| type | default | since | description |
| :-: | :-: | :-: | :-- |
| boolean | false | 1.2.0 | Enable automatic generation of table headers ids |

If enabled, generates automatic ids for table headers. Only applies if **[tables](https://github.com/showdownjs/showdown/wiki/Showdown-options#tables)** is enabled.

### ghCodeBlocks

[Permalink: ghCodeBlocks](https://github.com/showdownjs/showdown/wiki/Showdown-options#ghcodeblocks)

| type | default | since | description |
| :-: | :-: | :-: | :-- |
| boolean | true | 1.2.0 | Enable support for GFM code block style syntax (fenced codeblocks) |

**syntax**:

````
```
 some code here
 ```

````

NOTE: ghCodeBlocks are enabled by default since version 0.3.1

### tasklists\*\*:(boolean) \[default false\] Enable support for GFM takslists. Example

[Permalink: tasklists**:(boolean) [default false] Enable support for GFM takslists. Example:](https://github.com/showdownjs/showdown/wiki/Showdown-options#tasklistsboolean-default-false-enable-support-for-gfm-takslists-example)

| type | default | since | description |
| :-: | :-: | :-: | :-- |
| boolean | false | 1.2.0 | Enable support for GFM takslists |

Enables support for github style tasklists

**syntax**:

```html
 - [x] This task is done
 - [ ] This is still pending
```

### ghMentions

[Permalink: ghMentions](https://github.com/showdownjs/showdown/wiki/Showdown-options#ghmentions)

| type | default | since | description |
| :-: | :-: | :-: | :-- |
| boolean | false | 1.6.0 | Enable support for github @mentions |

Enables support for github @mentions, which links to the github profile page of the username mentioned

**input**:

```
hello there @tivie
```

**ghMentions** = false

```html
<p>hello there @tivie</p>
```

**ghMentions** = true

```html
<p>hello there <a href="https://www.github.com/tivie>@tivie</a></p>

```

### ghMentionsLink

[Permalink: ghMentionsLink](https://github.com/showdownjs/showdown/wiki/Showdown-options#ghmentionslink)

| type | default | since | description |
| :-: | :-: | :-: | :-- |
| boolean | `https://github.com/{u}` | 1.6.2 | Set link @mentions should point to |

Changes the link generated by @mentions. `{u}` is replaced by the text of the mentions. Only applies if **[ghMentions](https://github.com/showdownjs/showdown/wiki/Showdown-options#ghmentions)** is enabled.

**input**:

```html
hello there @tivie
```

**ghMentionsLink** = [https://github.com/{u}](https://github.com/%7Bu%7D)

```html
<p>hello there <a href="https://www.github.com/tivie>@tivie</a></p>

```

**ghMentionsLink** = [http://mysite.com/{u}/profile](http://mysite.com/%7Bu%7D/profile)

```html
<p>hello there <a href="//mysite.com/tivie/profile">@tivie</a></p>
```

### smoothLivePreview

[Permalink: smoothLivePreview](https://github.com/showdownjs/showdown/wiki/Showdown-options#smoothlivepreview)

| type | default | since | description |
| :-: | :-: | :-: | :-- |
| boolean | false | 1.2.1 | Fix weird effects due to parsing incomplete input |

On some circumstances, in live preview editors, when a paragraph is followed by a list it can cause an awkward effect.

![awkward effect](https://camo.githubusercontent.com/8db5b3813b6c6c8581464d48d7e31502a67031c2fc6dde07bb1e36a42ac23da3/687474703a2f2f692e696d6775722e636f6d2f5951396948544c2e676966254532253830253842)

You can prevent this by enabling this option

### smartIndentationFix

[Permalink: smartIndentationFix](https://github.com/showdownjs/showdown/wiki/Showdown-options#smartindentationfix)

| type | default | since | description |
| :-: | :-: | :-: | :-- |
| boolean | false | 1.4.2 | Fix indentation problems related to es6 template strings in the midst of indented code |

Tries to smartly fix indentation problems related to es6 template strings in the midst of indented code

### disableForced4SpacesIndentedSublists

[Permalink: disableForced4SpacesIndentedSublists](https://github.com/showdownjs/showdown/wiki/Showdown-options#disableforced4spacesindentedsublists)

| type | default | since | description |
| :-: | :-: | :-: | :-- |
| boolean | false | 1.5.0 | Disable the requirement of indenting sublists by 4 spaces for them to be nested |

Disables the requirement of indenting sublists by 4 spaces for them to be nested, effectively reverting to the old behavior where 2 or 3 spaces were enough.

**input**:

```html
- one
  - two

...

- one
    - two
```

**disableForced4SpacesIndentedSublists** = false

```html
<ul>
<li>one</li>
<li>two</li>
</ul>
<p>...</p>
<ul>
<li>one
 <ul>
  <li>two</li>
 </ul>
</li>
</ul>
```

**disableForced4SpacesIndentedSublists** = true

```html
<ul>
<li>one
 <ul>
  <li>two</li>
 </ul>
</li>
</ul>
<p>...</p>
<ul>
<li>one
 <ul>
  <li>two</li>
 </ul>
</li>
</ul>
```

### simpleLineBreaks

[Permalink: simpleLineBreaks](https://github.com/showdownjs/showdown/wiki/Showdown-options#simplelinebreaks)

| type | default | since | description |
| :-: | :-: | :-: | :-- |
| boolean | false | 1.5.1 | Parse line breaks as `<br/>` in paragraphs (like GitHub does) |

Every newline character inside paragraphs and spans is parsed as `<br/>`

**input**:

```
a line
wrapped in two
```

**simpleLineBreaks** = false

```html
<p>a line
wrapped in two</p>
```

**simpleLineBreaks** = true

```html
<p>a line<br>
wrapped in two</p>
```

### requireSpaceBeforeHeadingText

[Permalink: requireSpaceBeforeHeadingText](https://github.com/showdownjs/showdown/wiki/Showdown-options#requirespacebeforeheadingtext)

| type | default | since | description |
| :-: | :-: | :-: | :-- |
| boolean | false | 1.5.3 | Require a spance between `#` and header text |

Makes adding a space between `#` and the header text mandatory.

**input**:

```html
#header
```

**requireSpaceBeforeHeadingText** = false

```html
<h1 id="header">header</h1>
```

**simpleLineBreaks** = true

```html
<p>#header</p>
```

### encodeEmails

[Permalink: encodeEmails](https://github.com/showdownjs/showdown/wiki/Showdown-options#encodeemails)

| type | default | since | description |
| :-: | :-: | :-: | :-- |
| boolean | true | 1.6.1 | Enable e-mail address automatic obfuscation |

Enables e-mail addresses encoding through the use of Character Entities, transforming ASCII e-mail addresses into its equivalent decimal entities. (since v1.6.1)

NOTE: Prior to version 1.6.1, emails would always be obfuscated through dec and hex encoding.

**input**:

```html
<myself@example.com>

```

**encodeEmails** = false

```html
<a href="mailto:myself@example.com">myself@example.com</a>
```

**encodeEmails** = true

```html
<a href="&#109;&#97;&#105;&#108;t&#x6f;&#x3a;&#109;&#x79;s&#x65;&#x6c;&#102;&#64;&#x65;xa&#109;&#112;&#108;&#101;&#x2e;c&#x6f;&#109;">&#x6d;&#121;s&#101;&#108;f&#x40;&#x65;&#120;a&#x6d;&#x70;&#108;&#x65;&#x2e;&#99;&#x6f;&#109;</a>
```
