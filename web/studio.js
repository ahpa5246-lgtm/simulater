// Presentation only: retain the upstream engine and every native control.
const editor=document.getElementById('circuit-editor');
function applyTheme(){
 const doc=editor.contentDocument;if(!doc||!doc.body)return;
 doc.body.classList.add('circuitjs-app');
 if(!doc.getElementById('mina-studio-theme')){const link=doc.createElement('link');link.id='mina-studio-theme';link.rel='stylesheet';link.href='/design-system.css';doc.head.append(link);}
}
editor.addEventListener('load',applyTheme);
if(editor.contentDocument?.readyState==='complete')applyTheme();
