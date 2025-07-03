<script lang="ts">
  import { createEventDispatcher, onMount, onDestroy } from 'svelte';
  
  const dispatch = createEventDispatcher();
  
  let isListening: boolean = false;
  let recognition: any = null;
  let isSupported: boolean = false;
  let interimTranscript: string = '';
  let finalTranscript: string = '';
  let shouldListen: boolean = true;
  let restartTimeout: number;
  let isPaused: boolean = false;
  
  // Export functions to control listening from parent component
  export function pauseListening() {
    if (recognition && isListening) {
      isPaused = true;
      recognition.stop();
    }
  }
  
  export function resumeListening() {
    if (recognition && isPaused) {
      isPaused = false;
      recognition.start();
    }
  }
  
  onMount(() => {
    // Check if browser supports speech recognition
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    
    if (SpeechRecognition) {
      isSupported = true;
      recognition = new SpeechRecognition();
      if (recognition) {
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';
        
        recognition.onstart = () => {
          isListening = true;
          console.log('Speech recognition started - continuously listening');
        };
        
        recognition.onend = () => {
          isListening = false;
          console.log('Speech recognition ended');
          
          // Only restart if we should still be listening and not paused
          if (shouldListen && !isPaused) {
            restartTimeout = setTimeout(() => {
              if (shouldListen && recognition && !isPaused) {
                recognition.start();
              }
            }, 100);
          }
        };
        
        recognition.onresult = (event: any) => {
          let interim = '';
          let final = '';
          
          for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
              final += event.results[i][0].transcript;
            } else {
              interim += event.results[i][0].transcript;
            }
          }
          
          interimTranscript = interim;
          
          if (final) {
            finalTranscript = final;
            dispatch('transcript', { text: final.trim() });
            // Clear transcripts after dispatching
            setTimeout(() => {
              interimTranscript = '';
              finalTranscript = '';
            }, 100);
          }
        };
        
        recognition.onerror = (event: any) => {
          console.error('Speech recognition error:', event.error);
          isListening = false;
          
          // Restart after error (except if it's a permission error or paused)
          if (shouldListen && event.error !== 'not-allowed' && !isPaused) {
            restartTimeout = setTimeout(() => {
              if (shouldListen && recognition && !isPaused) {
                recognition.start();
              }
            }, 1000);
          }
        };
        
        // Start listening immediately
        recognition.start();
      }
    }
  });
  
  onDestroy(() => {
    shouldListen = false;
    if (restartTimeout) {
      clearTimeout(restartTimeout);
    }
    if (recognition && isListening) {
      recognition.stop();
    }
  });
</script>

{#if isSupported}
  <div class="speech-to-text">
    <div class="flex items-center gap-2 text-sm text-gray-300">
      {#if isPaused}
        <div class="h-2 w-2 rounded-full bg-orange-400"></div>
        <span>Paused while system speaks...</span>
      {:else if isListening}
        <div class="h-2 w-2 animate-pulse rounded-full bg-green-400"></div>
        <span>Listening...</span>
      {:else}
        <div class="h-2 w-2 rounded-full bg-gray-400"></div>
        <span>Voice recognition ready</span>
      {/if}
    </div>
    
    {#if interimTranscript || finalTranscript}
      <div class="mt-2 rounded-lg bg-white bg-opacity-10 p-3 border border-white border-opacity-20">
        <p class="text-sm text-gray-300">
          {finalTranscript}
          <span class="text-gray-400 italic">
            {interimTranscript}
          </span>
        </p>
      </div>
    {/if}
  </div>
{:else}
  <div class="text-sm text-gray-500">
    Speech recognition is not supported in this browser.
  </div>
{/if} 