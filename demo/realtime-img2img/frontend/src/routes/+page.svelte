<script lang="ts">
  import { onMount } from 'svelte';
  import type { Fields, PipelineInfo } from '$lib/types';
  import { PipelineMode } from '$lib/types';
  import ImagePlayer from '$lib/components/ImagePlayer.svelte';
  import VideoInput from '$lib/components/VideoInput.svelte';
  import ChatView from '$lib/components/ChatView.svelte';
  import Spinner from '$lib/icons/spinner.svelte';
  import Warning from '$lib/components/Warning.svelte';
  import { lcmLiveStatus, lcmLiveActions, LCMLiveStatus } from '$lib/lcmLive';
  import { mediaStreamActions, onFrameChangeStore } from '$lib/mediaStream';
  import { getPipelineValues, deboucedPipelineValues, pipelineValues } from '$lib/store';

  let pipelineParams: Fields;
  let pipelineInfo: PipelineInfo;
  let pageContent: string;
  let isImageMode: boolean = false;
  let maxQueueSize: number = 0;
  let currentQueueSize: number = 0;
  let queueCheckerRunning: boolean = false;
  let warningMessage: string = '';
  
  onMount(() => {
    getSettings();
  });

  async function getSettings() {
    const settings = await fetch('/api/settings').then((r) => r.json());
    pipelineParams = settings.input_params.properties;
    pipelineInfo = settings.info.properties;
    isImageMode = pipelineInfo.input_mode.default === PipelineMode.IMAGE;
    maxQueueSize = settings.max_queue_size;
    pageContent = settings.page_content;
    console.log(pipelineParams);
    toggleQueueChecker(true);
    
    // Auto-start the LCM live when page loads
    await startLcmLive();
  }

  // Handle new prompts from chat
  function handleNewPrompt(event: CustomEvent) {
    const { prompt } = event.detail;
    // Update the pipeline values store with the new prompt
    pipelineValues.update(values => ({
      ...values,
      prompt: prompt
    }));
  }

  function toggleQueueChecker(start: boolean) {
    queueCheckerRunning = start && maxQueueSize > 0;
    if (start) {
      getQueueSize();
    }
  }
  
  async function getQueueSize() {
    if (!queueCheckerRunning) {
      return;
    }
    const data = await fetch('/api/queue').then((r) => r.json());
    currentQueueSize = data.queue_size;
    setTimeout(getQueueSize, 10000);
  }

  function getSreamdata() {
    if (isImageMode) {
      return [getPipelineValues(), $onFrameChangeStore?.blob];
    } else {
      return [$deboucedPipelineValues];
    }
  }

  $: isLCMRunning = $lcmLiveStatus !== LCMLiveStatus.DISCONNECTED;
  $: if ($lcmLiveStatus === LCMLiveStatus.TIMEOUT) {
    warningMessage = 'Session timed out. Please try again.';
  }
  
  async function startLcmLive() {
    try {
      if (isImageMode) {
        await mediaStreamActions.enumerateDevices();
        await mediaStreamActions.start();
      }
      await lcmLiveActions.start(getSreamdata);
      toggleQueueChecker(false);
    } catch (e) {
      warningMessage = e instanceof Error ? e.message : '';
      toggleQueueChecker(true);
    }
  }
</script>

<svelte:head>
  <script
    src="https://cdnjs.cloudflare.com/ajax/libs/iframe-resizer/4.3.9/iframeResizer.contentWindow.min.js"
  ></script>
</svelte:head>

<!-- Fullscreen container -->
<div class="fullscreen-container">
  <Warning bind:message={warningMessage}></Warning>
  
  {#if pipelineParams}
    <!-- Fullscreen Image Player -->
    <div class="fullscreen-image">
      <ImagePlayer />
    </div>

    <!-- Video Input (small overlay if in image mode) -->
    {#if isImageMode}
      <div class="video-input-overlay">
        <VideoInput
          width={Number(pipelineParams.width.default)}
          height={Number(pipelineParams.height.default)}
        />
      </div>
    {/if}

    <!-- Chat Overlay - Centered on page -->
    <div class="chat-overlay-centered">
      <ChatView on:newPrompt={handleNewPrompt} />
    </div>

  {:else}
    <!-- loading -->
    <div class="flex items-center justify-center h-screen text-2xl">
      <Spinner classList={'animate-spin opacity-50'}></Spinner>
      <p>Loading...</p>
    </div>
  {/if}
</div>

<style lang="postcss">
  :global(html) {
    @apply text-black dark:bg-gray-900 dark:text-white;
  }

  .fullscreen-container {
    @apply fixed inset-0 w-full h-full bg-black;
  }

  .fullscreen-image {
    @apply absolute inset-0 w-full h-full flex items-center justify-center;
  }

  .fullscreen-image :global(.relative) {
    @apply !static w-full h-full !max-w-none flex items-center justify-center;
  }

  .fullscreen-image :global(img) {
    @apply max-w-full max-h-full object-contain !aspect-auto !rounded-none;
    width: 100vw;
    height: 100vh;
    object-fit: contain;
  }

  .chat-overlay-centered {
    @apply absolute inset-0 flex items-center justify-center z-20 pointer-events-none;
  }

  .chat-overlay-centered :global(.chat-view) {
    @apply pointer-events-auto;
    max-width: 600px;
    width: 90%;
  }

  .video-input-overlay {
    @apply absolute top-4 left-4 z-10 rounded-lg overflow-hidden shadow-lg;
    width: 240px;
    height: 135px; /* 16:9 aspect ratio */
  }

  /* Mobile responsive adjustments */
  @media (max-width: 768px) {
    .chat-overlay-centered :global(.chat-view) {
      max-width: 90%;
      width: 95%;
    }
    
    .video-input-overlay {
      @apply top-2 left-2;
      width: 160px;
      height: 90px; /* 16:9 aspect ratio for mobile */
    }
  }
</style>
