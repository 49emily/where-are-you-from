<script lang="ts">
  import { createEventDispatcher, onMount } from 'svelte';
  import SpeechToText from './SpeechToText.svelte';
  
  const dispatch = createEventDispatcher();
  
  interface ChatMessage {
    id: string;
    text: string;
    isUser: boolean;
    timestamp: Date;
  }
  
  let messages: ChatMessage[] = [];
  let textInput: string = '';
  let chatContainer: HTMLElement;
  let currentPromptIndex = 0;
  let waitingForUserResponse = false;
  let isPlayingAudio = false;
  let conversationStarted = false;
  let speechToTextComponent: SpeechToText;
  let streamingMessageId: string | null = null;
  let streamingText: string = '';
  let streamingInterval: number | null = null;
  
  // Conversation starter prompts
  const conversationStarters = [
    "what did you eat for breakfast?",
    "what did you do on sunday?", 
    "where did you first fall in love?",
    "what do you dream about?",
    "where are your parents from?",
    "where are you from?",
  ];
  
  function startConversation() {
    conversationStarted = true;
    // Start with the first prompt after a brief delay
    setTimeout(() => {
      showNextPrompt();
    }, 500);
  }
  
  function showNextPrompt() {
    // Reset to beginning if we've gone through all prompts
    if (currentPromptIndex >= conversationStarters.length) {
      currentPromptIndex = 0;
    }
    
    const prompt = conversationStarters[currentPromptIndex];
    addMessage(prompt, false); // false = system message
    waitingForUserResponse = true;
    currentPromptIndex++;
  }
  
  async function speakTextWithOpenAI(text: string) {
    try {
      isPlayingAudio = true;
      
      // Start streaming the text
      startTextStreaming(text);
      
      // Pause speech recognition before speaking
      if (speechToTextComponent) {
        speechToTextComponent.pauseListening();
      }
      
      const response = await fetch('https://api.openai.com/v1/audio/speech', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${import.meta.env.VITE_OPENAI_API_KEY || ''}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: 'tts-1',
          input: text,
          voice: 'nova', // Natural female voice
          response_format: 'mp3',
          speed: 0.9
        }),
      });
      
      if (response.ok) {
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        
        audio.onended = () => {
          URL.revokeObjectURL(audioUrl);
          isPlayingAudio = false;
          stopTextStreaming();
          
          // Resume speech recognition after speaking
          if (speechToTextComponent) {
            setTimeout(() => {
              speechToTextComponent.resumeListening();
            }, 500); // Small delay to avoid echo
          }
        };
        
        audio.onerror = () => {
          URL.revokeObjectURL(audioUrl);
          isPlayingAudio = false;
          stopTextStreaming();
          
          // Resume speech recognition on error
          if (speechToTextComponent) {
            speechToTextComponent.resumeListening();
          }
          console.error('Error playing audio');
        };
        
        await audio.play();
      } else {
        console.error('OpenAI TTS API error:', response.status);
        isPlayingAudio = false;
        stopTextStreaming();
        
        // Resume speech recognition if API fails
        if (speechToTextComponent) {
          speechToTextComponent.resumeListening();
        }
        // Fallback to browser TTS if available
        fallbackTTS(text);
      }
    } catch (error) {
      console.error('Error with OpenAI TTS:', error);
      isPlayingAudio = false;
      stopTextStreaming();
      
      // Resume speech recognition on error
      if (speechToTextComponent) {
        speechToTextComponent.resumeListening();
      }
      // Fallback to browser TTS if available
      fallbackTTS(text);
    }
  }
  
  function startTextStreaming(fullText: string) {
    if (messages.length === 0) return;
    
    const lastMessage = messages[messages.length - 1];
    if (lastMessage.isUser) return;
    
    streamingMessageId = lastMessage.id;
    streamingText = '';
    
    // Calculate timing: aim for text to finish slightly before audio
    const estimatedSpeechDuration = (fullText.length * 60) + 1000; // ~60ms per char + 1s buffer
    const charDelay = estimatedSpeechDuration / fullText.length;
    
    let currentIndex = 0;
    
    streamingInterval = setInterval(() => {
      if (currentIndex < fullText.length) {
        streamingText = fullText.substring(0, currentIndex + 1);
        currentIndex++;
      } else {
        stopTextStreaming();
      }
    }, Math.max(charDelay, 50)); // Minimum 50ms between characters
  }
  
  function stopTextStreaming() {
    if (streamingInterval) {
      clearInterval(streamingInterval);
      streamingInterval = null;
    }
    streamingMessageId = null;
    streamingText = '';
  }
  
  function fallbackTTS(text: string) {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.9;
      utterance.pitch = 1.1;
      utterance.volume = 0.8;
      
      // Resume listening when fallback TTS ends
      utterance.onend = () => {
        stopTextStreaming();
        if (speechToTextComponent) {
          setTimeout(() => {
            speechToTextComponent.resumeListening();
          }, 500);
        }
      };
      
      utterance.onerror = () => {
        stopTextStreaming();
      };
      
      const voices = speechSynthesis.getVoices();
      const femaleVoice = voices.find(voice => 
        voice.name.toLowerCase().includes('female') || 
        voice.name.toLowerCase().includes('samantha') ||
        voice.name.toLowerCase().includes('karen') ||
        voice.name.toLowerCase().includes('zira')
      );
      
      if (femaleVoice) {
        utterance.voice = femaleVoice;
      }
      
      speechSynthesis.speak(utterance);
    } else {
      stopTextStreaming();
    }
  }
  
  function addMessage(text: string, isUser: boolean = true) {
    if (!text.trim()) return;
    
    const newMessage: ChatMessage = {
      id: Date.now().toString() + Math.random(),
      text: text.trim(),
      isUser,
      timestamp: new Date()
    };
    
    messages = [...messages, newMessage];
    
    // Speak system messages out loud using OpenAI TTS
    if (!isUser) {
      // Small delay to ensure message is rendered first
      setTimeout(() => {
        speakTextWithOpenAI(text.trim());
      }, 100);
    }
    
    // If user responded and we're waiting for a response, show next prompt
    if (isUser && waitingForUserResponse) {
      waitingForUserResponse = false;
      // Wait a bit before showing next prompt
      setTimeout(() => {
        showNextPrompt();
      }, 15000);
    }
    
    // Emit the latest user message as prompt
    if (isUser) {
      dispatch('newPrompt', { prompt: text.trim() });
    }
    
    // Scroll to bottom
    setTimeout(() => {
      if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
      }
    }, 50);
  }
  
  function handleSpeechTranscript(event: CustomEvent) {
    const { text } = event.detail;
    addMessage(text, true);
  }
  
  function handleTextSubmit() {
    if (textInput.trim()) {
      addMessage(textInput, true);
      textInput = '';
    }
  }
  
  function handleKeyPress(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleTextSubmit();
    }
  }
  
  function clearChat() {
    // Stop any ongoing speech
    if ('speechSynthesis' in window) {
      speechSynthesis.cancel();
    }
    
    messages = [];
    currentPromptIndex = 0;
    waitingForUserResponse = false;
    isPlayingAudio = false;
    
    // Restart conversation from beginning
    setTimeout(() => {
      showNextPrompt();
    }, 1000);
  }
</script>

<div class="chat-view flex h-screen w-screen flex-col fixed inset-0">
  {#if !conversationStarted}
    <!-- Start Screen -->
    <div class="flex-1 flex items-center justify-center">
      <button 
        on:click={startConversation}
        class="px-8 py-4 bg-white bg-opacity-20 text-white rounded-xl hover:bg-opacity-30 transition-all text-lg font-medium border border-white border-opacity-20"
      >
        Begin
      </button>
    </div>
  {:else}
    <!-- Chat Messages -->
    <div 
      bind:this={chatContainer}
      class="flex-1 overflow-y-auto flex flex-col justify-end relative"
    >
      {#each messages as message (message.id)}
        <div class="mb-8 w-full">
          <p class="text-9xl leading-none font-light {message.isUser ? 'text-right pr-8 text-black w-2/5 ml-auto' : 'text-left pl-8 text-white w-2/5'}">
            {#if !message.isUser && streamingMessageId === message.id}
              {streamingText}<span class="animate-pulse">|</span>
            {:else}
              {message.text}
            {/if}
          </p>
          <!-- <p class="mt-3 text-sm text-gray-400 opacity-60 {message.isUser ? 'text-right pr-8' : 'text-left pl-8'}">
            {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </p> -->
        </div>
      {/each}
    </div>
    
    <!-- Input Area -->
    <div class="p-4 relative z-10">
      
      <!-- Text Input -->
      <!-- <div class="mb-3 flex gap-2">
        <input
          bind:value={textInput}
          on:keypress={handleKeyPress}
          placeholder="Enter your prompt..."
          class="flex-1 rounded-lg border border-white border-opacity-20 px-3 py-2 text-sm bg-white bg-opacity-10 text-white placeholder-gray-300 focus:bg-opacity-15 focus:border-opacity-30 focus:outline-none transition-all"
        />
      </div> -->
      
      <!-- Speech Input -->
      <div class="text-center">
        <SpeechToText bind:this={speechToTextComponent} on:transcript={handleSpeechTranscript} />
        {#if isPlayingAudio}
          <div class="mt-2 text-xs text-blue-400 flex items-center justify-center gap-2">
            <div class="h-1 w-1 animate-pulse rounded-full bg-blue-400"></div>
            <span>Speaking...</span>
          </div>
        {/if}
      </div>
    </div>
  {/if}
</div>

<style>
  .chat-view {
    /* Remove height restrictions to allow full screen */
  }
</style> 