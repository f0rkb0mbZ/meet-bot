// 1. Build your regex once
const joinedRe = /\bjoined$/i;

// 2. Observer callback
function onMutations(mutationsList) {
  for (const mutation of mutationsList) {
    // We only care about nodes being added
    if (mutation.type !== 'childList' || mutation.addedNodes.length === 0) 
      continue;

    for (const node of mutation.addedNodes) {
      // If it’s an element, grab its text; if it’s a text node, use it directly
      const text = (node.nodeType === Node.TEXT_NODE)
        ? node.nodeValue
        : node.textContent;

      if (text && joinedRe.test(text.trim())) {
        console.log('Someone joined! Text matched “joined”:', text.trim());
        // fire your notification or message here…
        return;  // stop once we’ve detected one
      }
    }
  }
}

// 3. Create & attach the observer
const observer = new MutationObserver(onMutations);
observer.observe(document.body, {
  childList: true,
  subtree: true
});
