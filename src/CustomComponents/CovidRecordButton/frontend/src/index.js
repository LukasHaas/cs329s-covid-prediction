import { Streamlit } from "streamlit-component-lib"
import AudioRecorder from 'audio-recorder-polyfill'
window.MediaRecorder = AudioRecorder

// Add text and a button to the DOM. (You could also add these directly
// to index.html.)
const span = document.body.appendChild(document.createElement("span"))
const button = span.appendChild(document.createElement("button"))

button.classList.add("covid-button");
button.textContent = "Start Recording"

// Add a click handler to our button. It will send data back to Streamlit.
let recorder = null;
let duration = 5000;
let timer = null;

button.onclick = function() {
  // Streamlit via `Streamlit.setComponentValue`.
  // Request permissions to record audio
  navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
    recorder = new MediaRecorder(stream) // MediaRecorder

    // Set record to <audio> when recording will be finished
    recorder.addEventListener('dataavailable', e => {
      var arrayBuffer;
      var reader = new FileReader();
      reader.onload = function(event) {
        arrayBuffer = new Uint8Array(event.target.result);
        arrayBuffer = Array.from(arrayBuffer);
        let blobURL = URL.createObjectURL(e.data)
        Streamlit.setComponentValue(JSON.stringify({"data": arrayBuffer, "url": blobURL})) //     Object({'url': blobURL, 'data': }))
      };
      reader.readAsArrayBuffer(e.data);
    })

    if (timer !== null) {
      clearTimeout(timer);
    }

    // Start recording
    recorder.start()
    button.textContent = 'Restart Recording'
    Streamlit.setComponentValue('clicked')

    // Triger stop after delay
    timer = setTimeout(stopRecording, duration)
  })
}

function stopRecording() {
  // Stop recording
  recorder.stop()
  button.textContent = "Start Recording"

  // Remove “recording” icon from browser tab
  recorder.stream.getTracks().forEach(i => i.stop())
}

/**
 * The component's render function. This will be called immediately after
 * the component is initially loaded, and then again every time the
 * component gets new data from Python.
 */
function onRender(event) {
  // Get the RenderData from the event
  const data = event.detail

  // Disable our button if necessary.
  button.disabled = data.disabled

  // Get component recording duration
  duration = data.args["duration"]

  // We tell Streamlit to update our frameHeight after each render event, in
  // case it has changed. (This isn't strictly necessary for the example
  // because our height stays fixed, but this is a low-cost function, so
  // there's no harm in doing it redundantly.)
  Streamlit.setFrameHeight()
}

// Attach our `onRender` handler to Streamlit's render event.
Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRender)

// Tell Streamlit we're ready to start receiving data. We won't get our
// first RENDER_EVENT until we call this function.
Streamlit.setComponentReady()

// Finally, tell Streamlit to update our initial height. We omit the
// `height` parameter here to have it default to our scrollHeight.
Streamlit.setFrameHeight()
