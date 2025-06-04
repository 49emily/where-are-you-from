<script lang="ts">
  import { createEventDispatcher, onMount } from 'svelte';
  import Button from './Button.svelte';
  
  const dispatch = createEventDispatcher();
  
  let isListening: boolean = false;
  let recognition: any = null;
  let isSupported: boolean = false;
  let interimTranscript: string = '';
  let finalTranscript: string = '';
  
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
          console.log('Speech recognition started');
        };
        
        recognition.onend = () => {
          isListening = false;
          console.log('Speech recognition ended');
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
        };
      }
    }
  });
  
  function toggleListening() {
    if (!recognition) return;
    
    if (isListening) {
      recognition.stop();
    } else {
      recognition.start();
    }
  }
</script>

{#if isSupported}
  <div class="speech-to-text">
    <Button 
      on:click={toggleListening}
      classList={`transition-colors ${isListening 
        ? 'bg-red-500 hover:bg-red-600 text-white' 
        : 'bg-green-500 hover:bg-green-600 text-white'}`}
    >
      {#if isListening}
        <span class="flex items-center gap-2">
          <div class="h-2 w-2 animate-pulse rounded-full bg-white"></div>
          Stop Listening
        </span>
      {:else}
        🎤 Start Voice
      {/if}
    </Button>
    
    {#if interimTranscript || finalTranscript}
      <div class="mt-2 rounded-lg bg-gray-100 p-3 dark:bg-gray-800">
        <p class="text-sm text-gray-600 dark:text-gray-400">
          {interimTranscript}
          <span class="font-semibold text-gray-900 dark:text-white">
            {finalTranscript}
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