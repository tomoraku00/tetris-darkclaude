import { useState, useEffect, useRef, useCallback } from "react"
import "./App.css"

const API = "http://127.0.0.1:8765"

const BANNER = ` ██████╗  █████╗ ██████╗ ██╗  ██╗ ██████╗██╗      █████╗ ██╗   ██╗██████╗ ███████╗
 ██╔══██╗██╔══██╗██╔══██╗██║ ██╔╝██╔════╝██║     ██╔══██╗██║   ██║██╔══██╗██╔════╝
 ██║  ██║███████║██████╔╝█████╔╝ ██║     ██║     ███████║██║   ██║██║  ██║█████╗
 ██║  ██║██╔══██║██╔══██╗██╔═██╗ ██║     ██║     ██╔══██║██║   ██║██║  ██║██╔══╝
 ██████╔╝██║  ██║██║  ██║██║  ██╗╚██████╗███████╗██║  ██║╚██████╔╝██████╔╝███████╗
 ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝`
const MASCOT = `   █        █
   ██      ██
  ██▀██████▀██
  ██▄ ████ ▄██
████████████████
  ████████████
   █ █    █ █   `

const THINKING_VERBS = ["Thinking","Cooking","Brewing","Cogitating","Crunching","Pondering","Simmering","思考中","考え中","推論中","解析中","演算中","思索中","分析中"]

type MsgType = "user"|"assistant"|"tool_call"|"tool_result"|"error"|"info_kv"|"info"|"thinking"|"code"|"diff_add"|"diff_rm"|"diff_ctx"|"separator"
interface Msg { id:number; type:MsgType; text:string; name?:string; isError?:boolean; elapsed?:number; label?:string; valueClass?:string }
interface StatusInfo { model:string; vram_free:number; vram_used:number; base_url:string }
interface ApprovalData { id:string; title:string; command:string; emphasis:string }

let _id = 0
const mk = (type:MsgType, text:string, extra?:Partial<Msg>):Msg => ({id:_id++,type,text,...extra})
const mkKV = (label:string, value:string, valueClass:string):Msg => ({id:_id++,type:"info_kv",text:value,label,valueClass})

function MsgLine({msg}:{msg:Msg}) {
  if (msg.type === "info_kv") return (
    <div className="msg-info">
      <span className="info-label">{msg.label}</span>
      <span className={msg.valueClass}>{msg.text}</span>
    </div>
  )
  switch(msg.type){
    case "user": return <div className="msg-user"><span className="prompt-mark">{">"}  </span><span className="user-text">{msg.text}</span></div>
    case "thinking": return <div className="msg-thinking">✻ {msg.text}</div>
    case "tool_call": return <div className="msg-tool-call">⏺ {msg.name}({msg.text})</div>
    case "tool_result": return <div className={msg.isError?"msg-tool-err":"msg-tool-ok"}>  ⎿ {msg.text}{msg.elapsed!==undefined&&<span className="msg-elapsed">  ({msg.elapsed.toFixed(1)}s)</span>}</div>
    case "error": return <div className="msg-error">ERROR: {msg.text}</div>
    case "info": return <div className="msg-info-plain">{msg.text}</div>
    case "separator": return <div className="msg-separator">{msg.text}</div>
    case "code": return <div className="msg-code">{msg.text}</div>
    case "diff_add": return <div className="msg-diff-add">{msg.text}</div>
    case "diff_rm": return <div className="msg-diff-rm">{msg.text}</div>
    case "diff_ctx": return <div className="msg-diff-ctx">{msg.text}</div>
    default: return <div className="msg-assistant">{msg.text}</div>
  }
}

function ApprovalDialog({data,onDecide}:{data:ApprovalData;onDecide:(d:string)=>void}) {
  const [sel,setSel] = useState(0)
  const opts = ["Yes",`Yes, and always allow access to ${data.emphasis} from this project`,"No"]
  const decide = (i:number) => { const d=["allow_once","always_allow","deny"]; onDecide(d[i]) }
  useEffect(()=>{
    const h = (e:KeyboardEvent) => {
      if(e.key==="ArrowUp") setSel(s=>Math.max(0,s-1))
      if(e.key==="ArrowDown") setSel(s=>Math.min(2,s+1))
      if(e.key==="Enter") decide(sel)
      if(e.key==="1") decide(0)
      if(e.key==="2") decide(1)
      if(e.key==="3"||e.key==="Escape") decide(2)
    }
    window.addEventListener("keydown",h)
    return ()=>window.removeEventListener("keydown",h)
  },[sel])
  return (
    <div className="approval-wrap">
      <div className="approval-sep-top"/>
      <div className="approval-title">{data.title}</div>
      <pre className="approval-cmd">{data.command}</pre>
      <div className="approval-q">Do you want to proceed?</div>
      {opts.map((o,i)=>(
        <div key={i} className={i===sel?"appr-sel":"appr-opt"} onClick={()=>decide(i)}>
          {i===sel?"> ":"  "}{i+1}. {o}
        </div>
      ))}
      <div className="approval-sep-bot"/>
      <div className="approval-hint">Esc to cancel  ·  1/2/3 to select directly</div>
    </div>
  )
}

export default function App() {
  const [msgs,setMsgs] = useState<Msg[]>([])
  const [input,setInput] = useState("")
  const [thinking,setThinking] = useState(false)
  const [thinkingTxt,setThinkingTxt] = useState("")
  const [status,setStatus] = useState<StatusInfo>({model:"qwen3.6",vram_free:0,vram_used:0,base_url:""})
  const [elapsed,setElapsed] = useState(0)
  const [approval,setApproval] = useState<ApprovalData|null>(null)
  const abortCtrl = useRef<AbortController|null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const startRef = useRef(Date.now())
  const addMsg = useCallback((m:Msg)=>setMsgs(p=>[...p,m]),[])

  useEffect(()=>{
    fetch(`${API}/status`).then(r=>r.json()).then((d:StatusInfo)=>{
      setStatus(d)
      const header = [
        mk("info",""),
        mkKV(" version    ","v0.9-beta","info-ver"),
        mkKV(" model      ",d.model,"info-val"),
        mkKV(" server     ",d.base_url,"info-val"),
        mkKV(" phase      ","B-new (Tauri)","info-phase"),
        mk("info",""),
        mk("info"," Type /help for commands."),
        mk("info",""),
      ]
      fetch(`${API}/messages`).then(r=>r.json()).then((data:any)=>{ if(!d.show_history){data={messages:[]}}; 
        const history:Msg[] = []
        for(const m of (data.messages||[])){
          if(m.role==="user") history.push(mk("user",m.content))
          else if(m.role==="assistant"&&m.content) history.push(mk("assistant",m.content))
          else if(m.role==="tool"&&m.content) history.push(mk("tool_result",m.content,{name:m.name}))
        }
        if(history.length>0) history.unshift(mk("separator","─".repeat(40)))
        setMsgs([...header,...history])
      }).catch(()=>setMsgs(header))
    }).catch(()=>setMsgs([mk("error","API server not running. Run: python api/main.py")]))
  },[])

  useEffect(()=>{
    const t=setInterval(()=>setElapsed(Math.floor((Date.now()-startRef.current)/1000)),1000)
    return ()=>clearInterval(t)
  },[])

  useEffect(()=>{ bottomRef.current?.scrollIntoView({behavior:"auto"}) },[msgs])

  const m=Math.floor(elapsed/60), s=elapsed%60


  const handleStop = async () => {
    try { await fetch(`${API}/stop`, {method:"POST"}) } catch(e) {}
    abortCtrl.current?.abort()
    setThinking(false)
    setThinkingTxt("")
  }
  const send = async () => {
    if (thinking) {
      try { await fetch(`${API}/stop`, {method:"POST"}) } catch(e) {}
      abortCtrl.current?.abort()
      setThinking(false)
      setThinkingTxt("")
    }
    const text=input.trim()
    if(!text||thinking) return
    setInput("");if(inputRef.current){(inputRef.current as any).style.height="auto"}
    if(text==="/clear"){ await fetch(`${API}/clear`,{method:"POST"}); setMsgs([mk("info","  cleared")]); return }
    if(text==="/help"){
      addMsg(mk("info","Commands:"))
      addMsg(mk("info","  /exit /quit /bye  — 終了"))
      addMsg(mk("info","  /help             — このヘルプ"))
      addMsg(mk("info","  /clear            — 画面クリア"))
      addMsg(mk("info","  /plan             — 計画モード ON (ツール実行なし)"))
      addMsg(mk("info","  /go               — 計画モード OFF (実行開始)"))
      return
    }
    if(["/exit","/quit","/bye"].includes(text)){ window.close(); return }
    if(text==="/plan"){ await fetch(`${API}/plan_mode`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({mode:true})}); addMsg(mk("info","  Plan Mode ON - ツール実行なし、計画のみ出力 (/go で実行)")); return }
    if(text==="/go"){ await fetch(`${API}/plan_mode`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({mode:false})}); addMsg(mk("info","  Plan Mode OFF - 通常モードに戻りました")); return }

    addMsg(mk("user",text))
    const verb=THINKING_VERBS[Math.floor(Math.random()*THINKING_VERBS.length)]
    const thinkId=_id
    addMsg(mk("thinking",`${verb}...`))
    setThinking(true); setThinkingTxt(`✻ ${verb}`)

    try {
      abortCtrl.current = new AbortController()
      const res=await fetch(`${API}/chat`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:text}),signal:abortCtrl.current.signal})
      const reader=res.body!.getReader(); const dec=new TextDecoder(); let buf=""
      setMsgs(p=>p.filter(m=>m.id!==thinkId)); setThinkingTxt("")

      while(true){
        const {done,value}=await reader.read()
        if(done) break
        buf+=dec.decode(value,{stream:true})
        const lines=buf.split("\n"); buf=lines.pop()??""
        for(const line of lines){
          if(!line.startsWith("data: ")) continue
          const data=line.slice(6)
          if(data==="[DONE]") break
          let ev:any; try{ev=JSON.parse(data)}catch{continue}

          if(ev.type==="text"){
            let inCode=false
            for(const l of ev.content.split("\n")){
              if(l.trimStart().startsWith("```")){
                addMsg(mk("separator","─".repeat(60))); inCode=!inCode; continue
              }
              addMsg(mk(inCode?"code":"assistant", l))
            }
            addMsg(mk("info",""))
          } else if(ev.type==="tool_call"){
            const key=ev.args?.path??ev.args?.command??ev.args?.pattern??ev.args?.query??""
            const short=key.length>47?key.slice(0,44)+"...":key
            addMsg(mk("tool_call",short.replace(/\n/g,"↵"),{name:ev.name}))
          } else if(ev.type==="tool_result"){
            addMsg(mk("tool_result",ev.result.slice(0,100),{isError:ev.is_error,elapsed:ev.elapsed}))
          } else if(ev.type==="diff_add"){
            addMsg(mk("diff_add",ev.text||""))
          } else if(ev.type==="diff_rm"){
            addMsg(mk("diff_rm",ev.text||""))
          } else if(ev.type==="diff_ctx"){
            addMsg(mk("diff_ctx",ev.text||""))
          } else if(ev.type==="approval_needed"){
            setApproval(ev)
          }
        }
      }
    } catch(e:any){ if(e.name!=="AbortError") addMsg(mk("error",String(e))) }
    finally{ setThinking(false); setThinkingTxt(""); fetch(`${API}/status`).then(r=>r.json()).then(setStatus).catch(()=>{}); inputRef.current?.focus() }
  }


  useEffect(() => {
    if (!approval) return
    const onKey = (e: KeyboardEvent) => {
      if (['1','2','3','Escape','Enter'].includes(e.key)) {
        e.preventDefault()
        e.stopPropagation()
        if (e.key === '1' || e.key === 'Enter') handleApproval('yes')
        else if (e.key === '2') handleApproval('always')
        else if (e.key === '3' || e.key === 'Escape') handleApproval('no')
      }
    }
    window.addEventListener('keydown', onKey, true)
    return () => window.removeEventListener('keydown', onKey, true)
  }, [approval])

  const handleApproval = async (decision:string) => {
    if(!approval) return
    setApproval(null)
    await fetch(`${API}/approve`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({id:approval.id,decision})}).catch(()=>{})
    inputRef.current?.focus()
  }

  return (
    <div className="app">
      <div className="chat-log">
        <div className="banner-wrap">
          <pre className="banner-text">{"\n" + BANNER}</pre>
          <pre className="banner-mascot">{MASCOT}</pre>
        </div>
        {msgs.map(m=><MsgLine key={m.id} msg={m}/>)}
        <div ref={bottomRef}/>
      </div>
      {approval&&<ApprovalDialog data={approval} onDecide={handleApproval}/>}
      {!approval&&(
        <div className="input-wrap">
          <div className="sep-line"/>
          <div className="input-row">
            <span className="prompt-mark">{">"}  </span>
            <textarea ref={inputRef as any} className="chat-input" value={input}
              onChange={e=>{setInput(e.target.value);const t=e.target;t.style.height="auto";t.style.height=t.scrollHeight+"px"}}
              onKeyDown={e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();send()}}}
              autoFocus spellCheck={false} rows={1}/>
          </div>
          <div className="sep-line"/>
        </div>
      )}
      <div className="status-bar">
        <span className="st-val">{status.model}</span>
        <span className="st-muted"> · </span>
        <span className="st-mode">Phase A6 stabilization</span>
        <span className="st-muted">  ·  Ctrl+Y: copy mode</span>
        {thinkingTxt&&<><span className="st-muted"> · </span><span className="st-think">{thinkingTxt}</span></>}
        <span style={{flex:1}}/>
        <span className="st-muted">⏱ </span>
        <span className="st-val">{m}m {String(s).padStart(2,"0")}s</span>
      </div>
    </div>
  )
}
