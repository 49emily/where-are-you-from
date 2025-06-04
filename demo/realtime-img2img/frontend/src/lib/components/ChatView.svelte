<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import ChatBubble from './ChatBubble.svelte';
  import SpeechToText from './SpeechToText.svelte';
  import Button from './Button.svelte';
  
  export let maxMessages: number = 10;
  
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
  
  function addMessage(text: string, isUser: boolean = true) {
    if (!text.trim()) return;
    
    const newMessage: ChatMessage = {
      id: Date.now().toString(),
      text: text.trim(),
      isUser,
      timestamp: new Date()
    };
    
    messages = [...messages, newMessage];
    
    // Keep only the latest messages
    if (messages.length > maxMessages) {
      messages = messages.slice(-maxMessages);
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
    messages = [];
  }
</script>

<div class="chat-view flex h-96 flex-col">
  <!-- Chat Messages - No background, floating bubbles -->
  <div 
    bind:this={chatContainer}
    class="flex-1 overflow-y-auto p-3 flex flex-col justify-end"
  >
    {#if messages.length === 0}
      <div class="flex h-full items-center justify-center">
        <p class="text-center text-sm text-white bg-black bg-opacity-50 px-4 py-2 rounded-lg">
          Start a conversation by typing or using voice input.<br/>
          Your messages will become prompts for the AI model.
        </p>
      </div>
    {:else}
      {#each messages as message (message.id)}
        <ChatBubble 
          message={message.text}
          isUser={message.isUser}
          timestamp={message.timestamp}
        />
      {/each}
    {/if}
  </div>
  
  <!-- Input Area with semi-transparent background -->
  <div class="border-t-0 p-3 bg-black bg-opacity-70 backdrop-blur-sm rounded-lg mt-2">
    <!-- Clear button -->
    <div class="flex justify-center mb-3">
      <button 
        on:click={clearChat} 
        class="text-xs px-3 py-1 bg-gray-600 bg-opacity-70 text-white rounded-lg hover:bg-opacity-90 transition-all"
      >
        Clear Chat
      </button>
    </div>
    
    <!-- Text Input -->
    <div class="mb-3 flex gap-2">
      <input
        bind:value={textInput}
        on:keypress={handleKeyPress}
        placeholder="Type your prompt here..."
        class="flex-1 rounded-lg border border-gray-500 px-3 py-2 text-sm focus:border-blue-400 focus:outline-none bg-gray-800 bg-opacity-80 text-white placeholder-gray-300"
      />
      <button 
        on:click={handleTextSubmit} 
        class="px-4 py-2 bg-blue-600 bg-opacity-80 text-white rounded-lg hover:bg-opacity-100 transition-all"
      >
        Send
      </button>
    </div>
    
    <!-- Speech Input -->
    <div class="text-center">
      <SpeechToText on:transcript={handleSpeechTranscript} />
    </div>
  </div>
</div>

<style>
  .chat-view {
    min-height: 24rem;
    max-height: 32rem;
  }
</style> 