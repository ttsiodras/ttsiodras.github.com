window.___jsl=window.___jsl||{};
window.___jsl.h=window.___jsl.h||'r;gc\/23579912-2b1b2e17';
window.___jsl.l=[];
window.___gpq=[];
window.gapi=window.gapi||{};
window.gapi.plusone=window.gapi.plusone||(function(){
  function f(n){return function(){window.___gpq.push(n,arguments)}}
  return{go:f('go'),render:f('render')}})();
function __bsld(){var p=window.gapi.plusone=window.googleapisv0.plusone;var f;while(f=window.___gpq.shift()){
  p[f]&&p[f].apply(p,window.___gpq.shift())}
}
window['___jsl'] = window['___jsl'] || {};window['___jsl']['u'] = 'https:\/\/apis.google.com\/js\/plusone.js';window['___jsl']['f'] = ['plusone-unsupported'];(window['___jsl']['ci'] = (window['___jsl']['ci'] || [])).push({});var jsloader=window.jsloader||{};
var gapi=window.gapi||{};
(function(){function m(b,d,a){a=n(a).join(b);i.length>0&&(a+=d+n(i).join(b));return a}function n(b){b.sort();for(var d=1;b[d];)b[d]==b[d-1]?b.splice(d,1):++d;return b}function o(b,d){if(b&&d){if(g.c)throw"Cannot continue until a pending callback completes.";g.c=b;g.o=d}}function u(b){if((p||document.readyState)!="loading")return!1;if(typeof window.___gapisync!="undefined")return window.___gapisync;if(b&&(b=b.sync,typeof b!="undefined"))return b;for(var b=!1,d=document.getElementsByTagName("meta"),
a=0,c;c=!b&&d[a];++a)"generator"==c.getAttribute("name")&&"blogger"==c.getAttribute("content")&&(b=!0);return b}function q(b,d){var a;a=b;if(e==="r")a=a.match(v);else if(e==="m")a=a.match(w);else{var c=a.match(x);if((a=g.m)&&c){var c=c[2],f=c.lastIndexOf(a);a=(f==0||a.charAt(0)=="."||c.charAt(f-1)==".")&&c.length-a.length==f}else a=!1}if(!a)throw"Cannot load url "+b+".";u(d)?document.write('<script src="'+b+'"><\/script>'):(a=document.createElement("script"),a.setAttribute("src",b),document.getElementsByTagName("head")[0].appendChild(a))}
function r(b,d){e="";g=window.___jsl=window.___jsl||{};i=g.l=g.l||[];j=window.console||window.opera&&window.opera.postError;k=b;p=d;var a,c=k.match(y)||k.match(z);try{a=c?decodeURIComponent(c[2]):g.h}catch(f){}a&&(a=a.split(";"),e=a.shift(),h=e==="r"?"https://ssl.gstatic.com/webclient/js":e==="m"?"https://apis.google.com":a.shift(),l=a.shift(),s=(c=e==="d")&&a.shift()||"gcjs-3p",t=c&&a.shift()||"")}var y=/\?([^&#]*&)*jsh=([^&#]*)/,z=/#([^&]*&)*jsh=([^&]*)/,v=/^https:\/\/ssl.gstatic.com\/webclient\/js(\/[a-zA-Z0-9_\-,=]+)*\/[a-zA-Z0-9_\-\.:!]*$/,
w=/^https:\/\/apis.google.com(\/[a-zA-Z0-9_\-,=]+)*\/[a-zA-Z0-9_\-\.:!]*$/,x=/^(https?:)?\/\/([^/:@]*)(:[0-9]+)?\//,g,e,h,s,t,l,i,j,k,p;r(document.location.href);jsloader.load=function(b,d){var a;if(!b||b.length==0)j&&j.warn("Cannot load empty features.");else if(e==="d"){var c=b,c=(h[h.length-1]=="/"?h.substring(0,h.length-1):h)+"/"+m(":","!",c);c+=".js?container="+s+"&c=2&jsload=0";l&&(c+="&r="+l);t=="d"&&(c+="&debug=1");a=c}else e==="r"||e==="f"?a=h+"/"+l+"/"+m("__","--",b)+".js":e==="m"||e===
"n"?(c=b.join(",").replace(".","_").replace("-","_"),a=h+l.replace("__features__",c)):(c="Cannot respond for features ["+b.join(",")+"].",j&&j.warn(c));d=d||{};if(typeof d==="function"){var c=b,f=d;a?(o(f,1),q(a,void 0),i.push.apply(i,c)):f&&f()}else{(g.cu=g.cu||[]).push(d.config);var f=d.callback,c=b,k=d;a?(o(f,1),q(a,k),i.push.apply(i,c)):f&&f()}};jsloader.reinitialize_=function(b,d){r(b,d)}})();
gapi.load=function(a,b){jsloader.load(a.split(":"),b)};(window.gapi=window.gapi||{}).load=gapi.load;
gapi.load('plusone-unsupported', {'callback': window['__bsld']  });