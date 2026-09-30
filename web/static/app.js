/* Дракончик Тоору · Автор: Матиенко Антон Александрович · E-mail: Aspksa@yandex.ru */
const $ = id => document.getElementById(id);
let scope = 'work', selected = null;
const titles = {assistant:'Личный помощник',home:'Домашние проекты',work:'Рабочие проекты',mobile:'Мобильное приложение',update:'Обновление',settings:'Настройки'};
function feedback(message=''){$('feedback').textContent=message}
async function api(path, options={}){
  const response=await fetch('/api/v1/'+path,{...options,headers:options.body?{'Content-Type':'application/json'}:{}});
  const result=await response.json();if(!response.ok)throw Error(result.error||'Ошибка запроса');return result;
}
function setPage(page){
  feedback();$('title').textContent=titles[page];
  document.querySelectorAll('#menu button').forEach(b=>b.classList.toggle('active',b.dataset.page===page));
  document.querySelectorAll('.page').forEach(el=>el.classList.remove('active'));
  const target=page==='home'||page==='work'?'projects':page==='mobile'||page==='update'?'placeholder':page;
  $(target).classList.add('active');
  if(page==='home'||page==='work'){scope=page;$('project-heading').textContent=titles[page];selected=null;$('project-memory').classList.add('hidden');loadProjects()}
  if(page==='settings')loadStatus();
  if(target==='placeholder'){$('placeholder-title').textContent=titles[page];$('placeholder-text').textContent=page==='mobile'?'Android и iOS приложения запланированы для следующего этапа.':'Проверка и установка обновлений из GitHub запланированы для следующего этапа.'}
}
function empty(parent,text){const p=document.createElement('p');p.className='hint';p.textContent=text;parent.append(p)}
async function loadStatus(){
  const grid=$('status-grid');grid.replaceChildren();
  try{const s=await api('system/status');$('core-badge').textContent='✅ Ядро работает';$('core-badge').className='badge';
    $('ai-badge').textContent=s.ai.status==='ok'?'✅ Ollama доступна':'⚠️ AI не подключён';$('ai-badge').className='badge '+(s.ai.status==='ok'?'':'warn');
    [['Ядро',s.core],['SQLite',s.database],['Хранилище',s.storage],['AI',s.ai.status],['Модель',s.ai.selected||'не выбрана'],['Свободно',Math.round(s.free_bytes/1024/1024)+' МБ']].forEach(([label,value])=>{
      const card=document.createElement('div');card.className='status-item';const strong=document.createElement('strong');strong.textContent=label;const span=document.createElement('span');span.textContent=value;card.append(strong,span);grid.append(card)})
  }catch(e){$('core-badge').textContent='❌ Ядро недоступно';$('core-badge').className='badge warn';feedback(e.message)}
}
async function loadMemories(){const parent=$('memory-list');parent.replaceChildren();try{const r=await api('memory?scope=personal');if(!r.memories.length)empty(parent,'Пока нет записей.');r.memories.forEach(m=>addMemoryNode(parent,m))}catch(e){feedback(e.message)}}
function addMemoryNode(parent,m){const article=document.createElement('article');article.textContent=m.text;const small=document.createElement('small');small.textContent=new Date(m.created_at).toLocaleString('ru-RU');article.append(small);parent.append(article)}
async function loadProjects(){const parent=$('project-list');parent.replaceChildren();try{const r=await api('projects?scope='+scope);if(!r.projects.length)empty(parent,'В этой области пока нет проектов.');r.projects.forEach(p=>{const button=document.createElement('button');button.className='project-card';const name=document.createElement('strong');name.textContent=p.name;const label=document.createElement('small');label.textContent='Открыть память проекта →';button.append(name,label);button.onclick=()=>openProject(p);parent.append(button)})}catch(e){feedback(e.message)}}
async function openProject(project){selected=project;$('selected-project').textContent=project.name;$('project-memory').classList.remove('hidden');const parent=$('project-memory-list');parent.replaceChildren();try{const r=await api('memory?scope='+scope+'&project_id='+encodeURIComponent(project.id));if(!r.memories.length)empty(parent,'Память проекта пуста.');r.memories.forEach(m=>addMemoryNode(parent,m))}catch(e){feedback(e.message)}}
function form(id,handler){$(id).addEventListener('submit',async e=>{e.preventDefault();feedback();const button=e.target.querySelector('[type=submit]');button.disabled=true;try{await handler();e.target.reset()}catch(err){feedback(err.message)}finally{button.disabled=false}})}
document.querySelectorAll('#menu button').forEach(b=>b.onclick=()=>setPage(b.dataset.page));
$('refresh-status').onclick=loadStatus;$('close-project').onclick=()=>$('project-memory').classList.add('hidden');
form('memory-form',async()=>{await api('memory',{method:'POST',body:JSON.stringify({text:$('memory-text').value,scope:'personal'})});await loadMemories()});
form('project-form',async()=>{await api('projects',{method:'POST',body:JSON.stringify({name:$('project-name').value,scope})});await loadProjects()});
form('project-memory-form',async()=>{if(!selected)throw Error('Выберите проект');await api('memory',{method:'POST',body:JSON.stringify({text:$('project-memory-text').value,scope,project_id:selected.id})});await openProject(selected)});
form('chat-form',async()=>{const message=$('message').value;const log=$('chat-log');const mine=document.createElement('div');mine.className='bubble me';mine.textContent=message;log.append(mine);const r=await api('chat',{method:'POST',body:JSON.stringify({message,scope:'personal'})});const reply=document.createElement('div');reply.className='bubble';reply.textContent=r.reply;log.append(reply);log.scrollTop=log.scrollHeight});
loadStatus();loadMemories();
