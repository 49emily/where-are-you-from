<script lang="ts">
  export let message: string;
  export let isUser: boolean = true;
  export let timestamp: Date = new Date();
  
  $: formattedTime = timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
</script>

<div class="mb-3 flex {isUser ? 'justify-end' : 'justify-start'}">
  <div class="max-w-xs lg:max-w-md">
    <div 
      class="rounded-lg px-4 py-2 shadow-lg backdrop-blur-sm {isUser 
        ? 'bg-blue-600 bg-opacity-90 text-white border border-blue-400 border-opacity-30' 
        : 'bg-gray-800 bg-opacity-90 text-white border border-gray-600 border-opacity-30'}"
    >
      <p class="text-sm font-medium">{message}</p>
    </div>
    <p class="mt-1 text-xs text-white bg-black bg-opacity-40 px-2 py-1 rounded {isUser ? 'text-right' : 'text-left'}">
      {formattedTime}
    </p>
  </div>
</div> 