"use strict";(self.webpackChunkwebsite=self.webpackChunkwebsite||[]).push([[989],{5680:(e,t,n)=>{n.d(t,{xA:()=>c,yg:()=>y});var r=n(6540);function a(e,t,n){return t in e?Object.defineProperty(e,t,{value:n,enumerable:!0,configurable:!0,writable:!0}):e[t]=n,e}function o(e,t){var n=Object.keys(e);if(Object.getOwnPropertySymbols){var r=Object.getOwnPropertySymbols(e);t&&(r=r.filter((function(t){return Object.getOwnPropertyDescriptor(e,t).enumerable}))),n.push.apply(n,r)}return n}function s(e){for(var t=1;t<arguments.length;t++){var n=null!=arguments[t]?arguments[t]:{};t%2?o(Object(n),!0).forEach((function(t){a(e,t,n[t])})):Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(n)):o(Object(n)).forEach((function(t){Object.defineProperty(e,t,Object.getOwnPropertyDescriptor(n,t))}))}return e}function i(e,t){if(null==e)return{};var n,r,a=function(e,t){if(null==e)return{};var n,r,a={},o=Object.keys(e);for(r=0;r<o.length;r++)n=o[r],t.indexOf(n)>=0||(a[n]=e[n]);return a}(e,t);if(Object.getOwnPropertySymbols){var o=Object.getOwnPropertySymbols(e);for(r=0;r<o.length;r++)n=o[r],t.indexOf(n)>=0||Object.prototype.propertyIsEnumerable.call(e,n)&&(a[n]=e[n])}return a}var l=r.createContext({}),p=function(e){var t=r.useContext(l),n=t;return e&&(n="function"==typeof e?e(t):s(s({},t),e)),n},c=function(e){var t=p(e.components);return r.createElement(l.Provider,{value:t},e.children)},u="mdxType",d={inlineCode:"code",wrapper:function(e){var t=e.children;return r.createElement(r.Fragment,{},t)}},g=r.forwardRef((function(e,t){var n=e.components,a=e.mdxType,o=e.originalType,l=e.parentName,c=i(e,["components","mdxType","originalType","parentName"]),u=p(n),g=a,y=u["".concat(l,".").concat(g)]||u[g]||d[g]||o;return n?r.createElement(y,s(s({ref:t},c),{},{components:n})):r.createElement(y,s({ref:t},c))}));function y(e,t){var n=arguments,a=t&&t.mdxType;if("string"==typeof e||a){var o=n.length,s=new Array(o);s[0]=g;var i={};for(var l in t)hasOwnProperty.call(t,l)&&(i[l]=t[l]);i.originalType=e,i[u]="string"==typeof e?e:a,s[1]=i;for(var p=2;p<o;p++)s[p]=n[p];return r.createElement.apply(null,s)}return r.createElement.apply(null,n)}g.displayName="MDXCreateElement"},3294:(e,t,n)=>{n.r(t),n.d(t,{contentTitle:()=>s,default:()=>u,frontMatter:()=>o,metadata:()=>i,toc:()=>l});var r=n(8168),a=(n(6540),n(5680));const o={},s="Running on Linux",i={unversionedId:"gpt-researcher/getting-started/linux-deployment",id:"gpt-researcher/getting-started/linux-deployment",isDocsHomePage:!1,title:"Running on Linux",description:"This guide will walk you through the process of deploying GPT Researcher on a Linux server.",source:"@site/docs/gpt-researcher/getting-started/linux-deployment.md",sourceDirName:"gpt-researcher/getting-started",slug:"/gpt-researcher/getting-started/linux-deployment",permalink:"/docs/gpt-researcher/getting-started/linux-deployment",editUrl:"https://github.com/assafelovic/gpt-researcher/tree/master/docs/docs/gpt-researcher/getting-started/linux-deployment.md",tags:[],version:"current",frontMatter:{},sidebar:"docsSidebar",previous:{title:"Getting Started",permalink:"/docs/gpt-researcher/getting-started/getting-started"},next:{title:"PIP Package",permalink:"/docs/gpt-researcher/gptr/pip-package"}},l=[{value:"Server Requirements",id:"server-requirements",children:[],level:2},{value:"Deployment Steps",id:"deployment-steps",children:[{value:"Step 1: Update the System",id:"step-1-update-the-system",children:[],level:3},{value:"First, ensure your package index is up-to-date:",id:"first-ensure-your-package-index-is-up-to-date",children:[],level:3}],level:2}],p={toc:l},c="wrapper";function u(e){let{components:t,...n}=e;return(0,a.yg)(c,(0,r.A)({},p,n,{components:t,mdxType:"MDXLayout"}),(0,a.yg)("h1",{id:"running-on-linux"},"Running on Linux"),(0,a.yg)("p",null,"This guide will walk you through the process of deploying GPT Researcher on a Linux server."),(0,a.yg)("h2",{id:"server-requirements"},"Server Requirements"),(0,a.yg)("p",null,"The default Ubuntu droplet option on ",(0,a.yg)("a",{parentName:"p",href:"https://m.do.co/c/1a2af257efba"},"DigitalOcean")," works well, but this setup should work on any hosting service with similar specifications:"),(0,a.yg)("ul",null,(0,a.yg)("li",{parentName:"ul"},"2 GB RAM"),(0,a.yg)("li",{parentName:"ul"},"1 vCPU"),(0,a.yg)("li",{parentName:"ul"},"50 GB SSD Storage")),(0,a.yg)("p",null,"Here's a screenshot of the recommended Ubuntu machine specifications:"),(0,a.yg)("p",null,(0,a.yg)("img",{parentName:"p",src:"https://cdn.discordapp.com/attachments/1129340110916288553/1262372662299070504/Screen_Shot_2024-07-15_at_14.32.01.png?ex=66cf0c28&is=66cdbaa8&hm=c1798d9c37de585dc7df8558e92545144e31a2407d8a181cac7e8c16059fdcd6&",alt:"Ubuntu Server Specifications"})),(0,a.yg)("h2",{id:"deployment-steps"},"Deployment Steps"),(0,a.yg)("p",null,"After setting up your server, follow these steps to install Docker, Docker Compose, and Nginx."),(0,a.yg)("p",null,"Some more commands to achieve that:"),(0,a.yg)("h3",{id:"step-1-update-the-system"},"Step 1: Update the System"),(0,a.yg)("h3",{id:"first-ensure-your-package-index-is-up-to-date"},"First, ensure your package index is up-to-date:"),(0,a.yg)("pre",null,(0,a.yg)("code",{parentName:"pre",className:"language-bash"},'sudo apt update\n### Step 2: Install Git\n### Git is a version control system. Install it using:\n\nsudo apt install git -y\n\n### Verify the installation by checking the Git version:\ngit --version\n### Step 3: Install Docker\n### Docker is a platform for developing, shipping, and running applications inside containers.\n\n### Install prerequisites:\n\nsudo apt install apt-transport-https ca-certificates curl software-properties-common -y\n### Add Docker\u2019s official GPG key:\n\ncurl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg\n### Set up the stable repository:\n\necho "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null\n### Update the package index again and install Docker:\n\nsudo apt update\nsudo apt install docker-ce -y\n### Verify Docker installation:\n\nsudo systemctl status docker\n### Optionally, add your user to the docker group to run Docker without sudo:\n\nsudo usermod -aG docker ${USER}\n### Log out and back in for the group change to take effect.\n\nStep 4: Install Nginx\n### Nginx is a high-performance web server.\n\n### Install Nginx:\n\nsudo apt install nginx -y\n### Start and enable Nginx:\n\nsudo systemctl start nginx\nsudo systemctl enable nginx\n### Verify Nginx installation:\n\nsudo systemctl status nginx\n')),(0,a.yg)("p",null,"Here's your nginx config file:"),(0,a.yg)("pre",null,(0,a.yg)("code",{parentName:"pre",className:"language-bash"},"events {}\n\nhttp {\n   server {\n       listen 80;\n       server_name name.example;\n\n       location / {\n           proxy_pass http://localhost:3000;\n           proxy_http_version 1.1;\n           proxy_set_header Upgrade $http_upgrade;\n           proxy_set_header Connection 'upgrade';\n           proxy_set_header Host $host;\n           proxy_cache_bypass $http_upgrade;\n       }\n\n       location ~ ^/(ws|upload|files|outputs) {\n           proxy_pass http://localhost:8000;\n           proxy_http_version 1.1;\n           proxy_set_header Upgrade $http_upgrade;\n           proxy_set_header Connection \"Upgrade\";\n           proxy_set_header Host $host;\n       }\n   }\n}\n")),(0,a.yg)("p",null,"And the relevant commands:"),(0,a.yg)("pre",null,(0,a.yg)("code",{parentName:"pre",className:"language-bash"},"vim /etc/nginx/nginx.conf\n### Edit it to reflect above. Then verify all is good with:\n\nsudo nginx -t\n# If there are no errors:\n\nsudo systemctl restart nginx\n\n# Clone .env.example as .env\n# Run from root: \n\ndocker-compose up --build\n\n")))}u.isMDXComponent=!0}}]);