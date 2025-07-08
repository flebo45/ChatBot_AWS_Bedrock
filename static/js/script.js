var socketio = io();

const messages = document.getElementById("chat-body")
const textbox = document.getElementById("message")
const send_btn = document.getElementById("send-btn")
const clear_btn = document.getElementById("clear-btn")
const rag_switch = document.getElementById("rag-switch")
const guardrail_switch = document.getElementById("guardrails-switch")

rag_switch.addEventListener("change", () => {
    const isEnabled = rag_switch.checked;
    socketio.emit("switch_status", {
        type: "rag_status",
        status: isEnabled
    });
});

guardrail_switch.addEventListener("change", () => {
    const isEnabled = guardrail_switch.checked;
    socketio.emit("switch_status", {
        type: "guardrails_status",
        status: isEnabled
    });
});


clear_btn.addEventListener("click", function() {
    const answers = document.querySelectorAll(".answer");
    const chat_placeholder = document.getElementById("chat-placeholder")
    answers.forEach(answer => answer.remove());
    chat_placeholder.style.display = "block";
    socketio.emit("clear" , {clear: true})
});

const createUserMessage = (msg) => {
    const content = `
    <div class="answer right">
        <div class="avatar">
            <img src="/static/img/userLogo.png" alt="User">
        </div>
        <div class="text">
            ${msg}
        </div>
        <div class="time">${new Date().toLocaleString()}</div>
    </div>
    `;

    messages.insertAdjacentHTML("beforeend", content);
};

const createModelMessageContainer = (msg_id) => {
    const content = `
    <div class="answer left">
        <div class="avatar">
            <img src="/static/img/logoBedrock.png" alt="AWS Bedrock">
        </div>
        <div class="text" id="textbox_${msg_id}">
            
        </div>
        <div class="time">${new Date().toLocaleString()}</div>
    </div>
    `;

    messages.insertAdjacentHTML("beforeend", content);
};

let modelBuffer = "";
let flushThreshold = 50;
let insideCodeBlock = false; 

const createModelMessage = (msg, msg_id) => {
    const msg_box = document.getElementById("textbox_".concat(msg_id))

    modelBuffer += msg;

    /**
     * const codeBlockToggle = modelBuffer.match(/```/g);
    if (codeBlockToggle && codeBlockToggle.length % 2 === 1) {
        insideCodeBlock = !insideCodeBlock;
    }

    const isCodeBlockEnd = /```$/.test(modelBuffer.trim()) || /```\n?$/.test(modelBuffer);

    const flushNow = (!insideCodeBlock && (/[.?!]\s$/.test(modelBuffer) || /\n$/.test(modelBuffer) || modelBuffer.length >= flushThreshold)) || isCodeBlockEnd;

    if (flushNow) {
        msg_box.innerHTML += marked.parse(modelBuffer)
        modelBuffer = "";
    }
     */

     // Look for full code block boundaries
    // Match only complete lines with three backticks
    const codeBlockBoundary = /(^|\n)```/g;
    const matches = [...modelBuffer.matchAll(codeBlockBoundary)];

    if (matches.length % 2 === 1) {
        insideCodeBlock = true;
    } else {
        insideCodeBlock = false;
    }

    const flushNow = (!insideCodeBlock && /\n$/.test(modelBuffer)) || isCodeBlockEnd;

    if (flushNow) {
        msg_box.innerHTML += marked.parse(modelBuffer)
        modelBuffer = "";
    }

    
}

socketio.on("message", (data) => {
    if(data.start){
        //deactivate the send button
        send_btn.disabled = true;
        createModelMessageContainer(data.msg_id);
    }else if(data.stream){
        createModelMessage(data.stream, data.msg_id);
    }else if(!data.start){

        if(modelBuffer != "") {
            const msg_box = document.getElementById("textbox_".concat(data.msg_id));
            msg_box.innerHTML += marked.parse(modelBuffer)
            modelBuffer = ""
        }
        //activate the send button
        send_btn.disabled = false;

        
    }
    
})


textbox.addEventListener("keydown", function(event) {
    if(event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendMessage()
    }
})

const sendMessage = () => {
    const message = document.getElementById("message");
    const chat_placeholder = document.getElementById("chat-placeholder")
    if (message.value == "") return;

    chat_placeholder.style.display = "none";
    socketio.emit("message", {data: message.value})
    createUserMessage(message.value)
    message.value = "";
}

document.getElementById("model-select").addEventListener('change', function () {
    const selectedModel = this.value;
    socketio.emit('model_selected', {model : selectedModel});
});