<script lang="ts">
  import 'rvfc-polyfill';

  import { onDestroy, onMount } from 'svelte';
  import {
    mediaStreamStatus,
    MediaStreamStatusEnum,
    onFrameChangeStore,
    mediaStream,
    mediaDevices
  } from '$lib/mediaStream';
  import MediaListSwitcher from './MediaListSwitcher.svelte';
  export let width = 512;
  export let height = 512;
  
  // Calculate 16:9 aspect ratio based on the width
  const aspectRatio = 16 / 9;
  const canvasWidth = width;
  const canvasHeight = Math.round(width / aspectRatio);
  const size = { width: canvasWidth, height: canvasHeight };

  let videoEl: HTMLVideoElement;
  let canvasEl: HTMLCanvasElement;
  let ctx: CanvasRenderingContext2D;
  let videoFrameCallbackId: number;

  // ajust the throttle time to your needs
  const THROTTLE = 1000 / 120;
  let selectedDevice: string = '';
  let videoIsReady = false;

  onMount(() => {
    ctx = canvasEl.getContext('2d') as CanvasRenderingContext2D;
    canvasEl.width = size.width;
    canvasEl.height = size.height;
  });
  $: {
    console.log(selectedDevice);
  }
  onDestroy(() => {
    if (videoFrameCallbackId) videoEl.cancelVideoFrameCallback(videoFrameCallbackId);
  });

  $: if (videoEl) {
    videoEl.srcObject = $mediaStream;
  }
  let lastMillis = 0;
  async function onFrameChange(now: DOMHighResTimeStamp, metadata: VideoFrameCallbackMetadata) {
    if (now - lastMillis < THROTTLE) {
      videoFrameCallbackId = videoEl.requestVideoFrameCallback(onFrameChange);
      return;
    }
    const videoWidth = videoEl.videoWidth;
    const videoHeight = videoEl.videoHeight;
    
    // Calculate scaling to fit the video into the canvas while preserving aspect ratio
    const videoAspectRatio = videoWidth / videoHeight;
    const canvasAspectRatio = size.width / size.height;
    
    let drawWidth, drawHeight, offsetX, offsetY;
    
    if (videoAspectRatio > canvasAspectRatio) {
      // Video is wider than canvas - fit by height
      drawHeight = size.height;
      drawWidth = drawHeight * videoAspectRatio;
      offsetX = (size.width - drawWidth) / 2;
      offsetY = 0;
    } else {
      // Video is taller than canvas - fit by width
      drawWidth = size.width;
      drawHeight = drawWidth / videoAspectRatio;
      offsetX = 0;
      offsetY = (size.height - drawHeight) / 2;
    }
    
    // Clear canvas and draw video preserving aspect ratio
    ctx.clearRect(0, 0, size.width, size.height);
    ctx.drawImage(videoEl, offsetX, offsetY, drawWidth, drawHeight);
    
    const blob = await new Promise<Blob>((resolve) => {
      canvasEl.toBlob(
        (blob) => {
          resolve(blob as Blob);
        },
        'image/jpeg',
        1
      );
    });
    onFrameChangeStore.set({ blob });
    videoFrameCallbackId = videoEl.requestVideoFrameCallback(onFrameChange);
  }

  $: if ($mediaStreamStatus == MediaStreamStatusEnum.CONNECTED && videoIsReady) {
    videoFrameCallbackId = videoEl.requestVideoFrameCallback(onFrameChange);
  }
</script>

<div class="relative mx-auto max-w-lg overflow-hidden rounded-lg border border-slate-300">
  <div class="relative z-10 w-full" style="aspect-ratio: 16/9;">
    {#if $mediaDevices.length > 0}
      <div class="absolute bottom-0 right-0 z-10">
        <MediaListSwitcher />
      </div>
    {/if}
    <video
      class="pointer-events-none w-full h-full object-cover"
      bind:this={videoEl}
      on:loadeddata={() => {
        videoIsReady = true;
      }}
      playsinline
      autoplay
      muted
      loop
    ></video>
    <canvas bind:this={canvasEl} class="absolute left-0 top-0 w-full h-full object-cover"
    ></canvas>
  </div>
  <div class="absolute left-0 top-0 flex w-full h-full items-center justify-center">
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 448" class="w-40 p-5 opacity-20">
      <path
        fill="currentColor"
        d="M224 256a128 128 0 1 0 0-256 128 128 0 1 0 0 256zm-45.7 48A178.3 178.3 0 0 0 0 482.3 29.7 29.7 0 0 0 29.7 512h388.6a29.7 29.7 0 0 0 29.7-29.7c0-98.5-79.8-178.3-178.3-178.3h-91.4z"
      />
    </svg>
  </div>
</div>
