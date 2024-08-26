"use strict";(self.webpackChunkwebsite=self.webpackChunkwebsite||[]).push([[2663],{5680:(e,r,t)=>{t.d(r,{xA:()=>c,yg:()=>g});var n=t(6540);function l(e,r,t){return r in e?Object.defineProperty(e,r,{value:t,enumerable:!0,configurable:!0,writable:!0}):e[r]=t,e}function a(e,r){var t=Object.keys(e);if(Object.getOwnPropertySymbols){var n=Object.getOwnPropertySymbols(e);r&&(n=n.filter((function(r){return Object.getOwnPropertyDescriptor(e,r).enumerable}))),t.push.apply(t,n)}return t}function o(e){for(var r=1;r<arguments.length;r++){var t=null!=arguments[r]?arguments[r]:{};r%2?a(Object(t),!0).forEach((function(r){l(e,r,t[r])})):Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(t)):a(Object(t)).forEach((function(r){Object.defineProperty(e,r,Object.getOwnPropertyDescriptor(t,r))}))}return e}function i(e,r){if(null==e)return{};var t,n,l=function(e,r){if(null==e)return{};var t,n,l={},a=Object.keys(e);for(n=0;n<a.length;n++)t=a[n],r.indexOf(t)>=0||(l[t]=e[t]);return l}(e,r);if(Object.getOwnPropertySymbols){var a=Object.getOwnPropertySymbols(e);for(n=0;n<a.length;n++)t=a[n],r.indexOf(t)>=0||Object.prototype.propertyIsEnumerable.call(e,t)&&(l[t]=e[t])}return l}var s=n.createContext({}),p=function(e){var r=n.useContext(s),t=r;return e&&(t="function"==typeof e?e(r):o(o({},r),e)),t},c=function(e){var r=p(e.components);return n.createElement(s.Provider,{value:r},e.children)},u="mdxType",y={inlineCode:"code",wrapper:function(e){var r=e.children;return n.createElement(n.Fragment,{},r)}},m=n.forwardRef((function(e,r){var t=e.components,l=e.mdxType,a=e.originalType,s=e.parentName,c=i(e,["components","mdxType","originalType","parentName"]),u=p(t),m=l,g=u["".concat(s,".").concat(m)]||u[m]||y[m]||a;return t?n.createElement(g,o(o({ref:r},c),{},{components:t})):n.createElement(g,o({ref:r},c))}));function g(e,r){var t=arguments,l=r&&r.mdxType;if("string"==typeof e||l){var a=t.length,o=new Array(a);o[0]=m;var i={};for(var s in r)hasOwnProperty.call(r,s)&&(i[s]=r[s]);i.originalType=e,i[u]="string"==typeof e?e:l,o[1]=i;for(var p=2;p<a;p++)o[p]=t[p];return n.createElement.apply(null,o)}return n.createElement.apply(null,t)}m.displayName="MDXCreateElement"},9109:(e,r,t)=>{t.r(r),t.d(r,{contentTitle:()=>o,default:()=>u,frontMatter:()=>a,metadata:()=>i,toc:()=>s});var n=t(8168),l=(t(6540),t(5680));const a={sidebar_label:"html",title:"processing.html"},o=void 0,i={unversionedId:"reference/processing/html",id:"reference/processing/html",isDocsHomePage:!1,title:"processing.html",description:"HTML processing functions",source:"@site/docs/reference/processing/html.md",sourceDirName:"reference/processing",slug:"/reference/processing/html",permalink:"/docs/reference/processing/html",editUrl:"https://github.com/assafelovic/gpt-researcher/tree/master/docs/docs/reference/processing/html.md",tags:[],version:"current",frontMatter:{sidebar_label:"html",title:"processing.html"}},s=[{value:"extract_hyperlinks",id:"extract_hyperlinks",children:[],level:4},{value:"format_hyperlinks",id:"format_hyperlinks",children:[],level:4}],p={toc:s},c="wrapper";function u(e){let{components:r,...t}=e;return(0,l.yg)(c,(0,n.A)({},p,t,{components:r,mdxType:"MDXLayout"}),(0,l.yg)("p",null,"HTML processing functions"),(0,l.yg)("h4",{id:"extract_hyperlinks"},"extract","_","hyperlinks"),(0,l.yg)("pre",null,(0,l.yg)("code",{parentName:"pre",className:"language-python"},"def extract_hyperlinks(soup: BeautifulSoup,\n                       base_url: str) -> list[tuple[str, str]]\n")),(0,l.yg)("p",null,"Extract hyperlinks from a BeautifulSoup object"),(0,l.yg)("p",null,(0,l.yg)("strong",{parentName:"p"},"Arguments"),":"),(0,l.yg)("ul",null,(0,l.yg)("li",{parentName:"ul"},(0,l.yg)("inlineCode",{parentName:"li"},"soup")," ",(0,l.yg)("em",{parentName:"li"},"BeautifulSoup")," - The BeautifulSoup object"),(0,l.yg)("li",{parentName:"ul"},(0,l.yg)("inlineCode",{parentName:"li"},"base_url")," ",(0,l.yg)("em",{parentName:"li"},"str")," - The base URL")),(0,l.yg)("p",null,(0,l.yg)("strong",{parentName:"p"},"Returns"),":"),(0,l.yg)("p",null,"  List[Tuple","[str, str]","]: The extracted hyperlinks"),(0,l.yg)("h4",{id:"format_hyperlinks"},"format","_","hyperlinks"),(0,l.yg)("pre",null,(0,l.yg)("code",{parentName:"pre",className:"language-python"},"def format_hyperlinks(hyperlinks: list[tuple[str, str]]) -> list[str]\n")),(0,l.yg)("p",null,"Format hyperlinks to be displayed to the user"),(0,l.yg)("p",null,(0,l.yg)("strong",{parentName:"p"},"Arguments"),":"),(0,l.yg)("ul",null,(0,l.yg)("li",{parentName:"ul"},(0,l.yg)("inlineCode",{parentName:"li"},"hyperlinks")," ",(0,l.yg)("em",{parentName:"li"},"List[Tuple","[str, str]","]")," - The hyperlinks to format")),(0,l.yg)("p",null,(0,l.yg)("strong",{parentName:"p"},"Returns"),":"),(0,l.yg)("ul",null,(0,l.yg)("li",{parentName:"ul"},(0,l.yg)("inlineCode",{parentName:"li"},"List[str]")," - The formatted hyperlinks")))}u.isMDXComponent=!0}}]);