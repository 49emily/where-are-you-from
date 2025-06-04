<script lang="ts">
  export let message: string;
  export let isUser: boolean = true;
  export let timestamp: Date = new Date();
  
  $: formattedTime = timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
</script>

<div class="mb-3 flex {isUser ? 'justify-end' : 'justify-start'}">
  <div class="max-w-xs lg:max-w-md">
    <div 
      class="rounded-xl px-4 py-3 {isUser 
        ? 'bg-white bg-opacity-90 text-gray-800 border border-gray-200' 
        : 'bg-gray-100 bg-opacity-80 text-gray-700 border border-gray-300'}"
    >
      <p class="text-sm leading-relaxed">{message}</p>
    </div>
    <p class="mt-1 text-xs text-gray-400 {isUser ? 'text-right' : 'text-left'}">
      {formattedTime}
    </p>
  </div>
</div> 