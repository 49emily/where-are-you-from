<script lang="ts">
  import { onMount } from 'svelte';
  import type { Fields, PipelineInfo } from '$lib/types';
  import { PipelineMode } from '$lib/types';
  import ImagePlayer from '$lib/components/ImagePlayer.svelte';
  import VideoInput from '$lib/components/VideoInput.svelte';
  import Button from '$lib/components/Button.svelte';
  import PipelineOptions from '$lib/components/PipelineOptions.svelte';
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
  let showControls: boolean = true;
  
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
  let disabled = false;
  async function toggleLcmLive() {
    try {
      if (!isLCMRunning) {
        if (isImageMode) {
          await mediaStreamActions.enumerateDevices();
          await mediaStreamActions.start();
        }
        disabled = true;
        await lcmLiveActions.start(getSreamdata);
        disabled = false;
        toggleQueueChecker(false);
      } else {
        if (isImageMode) {
          mediaStreamActions.stop();
        }
        lcmLiveActions.stop();
        toggleQueueChecker(true);
      }
    } catch (e) {
      warningMessage = e instanceof Error ? e.message : '';
      disabled = false;
      toggleQueueChecker(true);
    }
  }

  function toggleControls() {
    showControls = !showControls;
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
      <ChatView on:newPrompt={handleNewPrompt} maxMessages={15} />
    </div>

    <!-- Controls Toggle Button -->
    <button 
      class="controls-toggle"
      on:click={toggleControls}
      title={showControls ? 'Hide Controls' : 'Show Controls'}
    >
      {showControls ? '⚙️' : '⚙️'}
    </button>

    <!-- Controls Panel -->
    {#if showControls}
      <div class="controls-panel">
        <div class="controls-content">
          {#if pageContent}
            <div class="text-center mb-4">
              {@html pageContent}
            </div>
          {/if}
          
    {#if maxQueueSize > 0}
            <p class="text-sm text-center mb-4">
        There are <span id="queue_size" class="font-bold">{currentQueueSize}</span>
        user(s) sharing the same GPU, affecting real-time performance. Maximum queue size is {maxQueueSize}.
        <a
          href="https://huggingface.co/spaces/radames/Real-Time-Latent-Consistency-Model?duplicate=true"
          target="_blank"
          class="text-blue-500 underline hover:no-underline">Duplicate</a
        > and run it on your own GPU.
      </p>
    {/if}

          <div class="flex flex-col gap-4">
            <Button on:click={toggleLcmLive} {disabled} classList={'text-lg p-2 w-full'}>
          {#if isLCMRunning}
            Stop
          {:else}
            Start
          {/if}
        </Button>
        <PipelineOptions {pipelineParams}></PipelineOptions>
      </div>
        </div>
      </div>
    {/if}

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

  .controls-toggle {
    @apply absolute bottom-4 left-4 z-30 bg-black bg-opacity-50 text-white p-3 rounded-full hover:bg-opacity-70 transition-all;
  }

  .controls-panel {
    @apply absolute bottom-4 left-16 z-20 bg-black bg-opacity-80 backdrop-blur-sm text-white rounded-lg p-4 max-w-md;
  }

  .controls-content {
    @apply space-y-4;
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
    
    .controls-panel {
      @apply bottom-2 left-2 right-2 max-w-none;
    }
    
    .controls-toggle {
      @apply bottom-2 left-1/2 transform -translate-x-1/2;
    }
  }
</style>
