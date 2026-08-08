function playVideo(id) {
    const v = currentQueue.find(item => item.id === id);
    activeVideo = v;

    document.getElementById('chipsBar').style.display = 'none';
    document.getElementById('videoGrid').style.display = 'none';
    document.getElementById('watchContainer').style.display = 'flex';

    if(isMiniplayerActive) maximizeFromMiniplayer();

    showLoader("Fetching media link...");

    // Fetch direct stream link from endpoint
    fetch(`/api/stream-video?q=${encodeURIComponent(id)}`)
        .then(res => res.json())
        .then(data => {
            hideLoader();
            if(data.error || !data.url) {
                alert("Failed to load stream URL.");
                return;
            }
            
            const videoNode = document.getElementById('mainVideo');
            videoNode.src = data.url;
            videoNode.play().catch(e => console.log("Autoplay blocked:", e));
        })
        .catch(() => {
            hideLoader();
            alert("Error connecting to server.");
        });
    
    if(v) {
        document.getElementById('videoTitle').innerText = v.title;
        document.getElementById('videoUploader').innerText = `Channel: ${v.uploader}`;
    }

    renderUpNext(id);
}
