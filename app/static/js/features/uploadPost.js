// Upload Post Feature

let tagAutocomplete = null;
let tagList = null;

export function initUploadPostFeature() {
  console.log('[UPLOAD POST] Starting feature initialization');
  
  const modal = document.getElementById('uploadModal');
  const openBtn = document.getElementById('openUploadBtn');
  const closeBtn = document.getElementById('closeUploadBtn');
  const cancelBtn = document.getElementById('cancelUploadBtn');
  const uploadForm = document.getElementById('uploadForm');
  const photoInput = document.getElementById('photoInput');
  const preview = document.getElementById('preview');

  console.log('[UPLOAD POST] Elements found:', {
    modal: !!modal,
    openBtn: !!openBtn,
    closeBtn: !!closeBtn,
    cancelBtn: !!cancelBtn,
    uploadForm: !!uploadForm,
    photoInput: !!photoInput,
    preview: !!preview
  });

  if (!modal || !openBtn) {
    console.error('[UPLOAD POST] Required elements not found! Modal:', !!modal, 'OpenBtn:', !!openBtn);
    return;
  }

  console.log('[UPLOAD POST] Initializing upload post feature');

  // Open button
  openBtn.addEventListener('click', () => {
    console.log('[UPLOAD POST] Open button clicked');
    modal.classList.add('open');
    loadTags();
  });

  // Close/Cancel buttons
  closeBtn.addEventListener('click', () => {
    console.log('[UPLOAD POST] Close button clicked');
    modal.classList.remove('open');
    resetForm();
  });

  cancelBtn.addEventListener('click', () => {
    console.log('[UPLOAD POST] Cancel button clicked');
    modal.classList.remove('open');
    resetForm();
  });

  // Click outside modal
  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      console.log('[UPLOAD POST] Clicked outside modal');
      modal.classList.remove('open');
      resetForm();
    }
  });

  // File input handling
  photoInput.addEventListener('change', function() {
    preview.innerHTML = '';
    
    const file = this.files[0];
    console.log('[UPLOAD POST] File selected:', {
      name: file?.name,
      type: file?.type,
      size: file?.size
    });
    
    if (file && file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = function(e) {
        const box = document.createElement('div');
        box.className = 'image-box';
        
        const img = document.createElement('img');
        img.src = e.target.result;
        
        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'remove-btn';
        removeBtn.innerHTML = '×';
        removeBtn.onclick = (e) => {
          e.preventDefault();
          photoInput.value = '';
          preview.innerHTML = '';
        };
        
        box.appendChild(img);
        box.appendChild(removeBtn);
        preview.appendChild(box);
      };
      reader.readAsDataURL(file);
    }
  });

  // Form submission
  uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    console.log('[UPLOAD POST] Form submission started');
    
    if (!photoInput.files.length) {
      showError('Please select a photo');
      return;
    }
    
    const file = photoInput.files[0];
    const selectedTags = tagList ? tagList.get_items() : [];
    
    if (!selectedTags.length) {
      showError('Please select at least one tag');
      return;
    }
    
    // Get image dimensions
    const img = new Image();
    img.onload = () => {
      submitUpload(file, selectedTags.map(t => t.id), img.width, img.height);
    };
    img.onerror = () => {
      showError('Invalid image file');
    };
    img.src = URL.createObjectURL(file);
  });

  console.log('[UPLOAD POST] Feature initialization complete');
}

async function loadTags() {
  console.log('[UPLOAD POST] Loading tags');
  try {
    const response = await fetch('/api/discover/search_items');
    const data = await response.json();
    const tags = data.items.filter(item => item.type === 'tag');
    
    // Initialize tag list
    if (!tagList) {
      tagList = new window.TagList({
        mountEl: document.getElementById('selectedTagsContainer'),
        initialItems: []
      });
    }
    
    // Initialize autocomplete
    if (!tagAutocomplete) {
      tagAutocomplete = window.createSearchBarAutocomplete(
        document.getElementById('tagSearchContainer'),
        (selectedItem) => {
          tagList.add_item(selectedItem);
        },
        tags,
        { placeholder: 'Search and select tags...' }
      );
    } else {
      tagAutocomplete.setItems(tags);
    }
    
  } catch (error) {
    console.error('[UPLOAD POST] Error loading tags:', error);
    showError('Failed to load tags');
  }
}

async function submitUpload(file, tagIds, width, height) {
  try {
    showLoading(true);
    hideMessages();
    
    const formData = new FormData();
    formData.append('photo', file);
    formData.append('width', width);
    formData.append('height', height);
    formData.append('tag_ids', tagIds.join(','));
    
    const response = await fetch('/api/photos/upload', {
      method: 'POST',
      body: formData
    });
    
    const data = await response.json();
    
    if (!response.ok) {
      showError(data.error || 'Upload failed');
      return;
    }
    
    showSuccess('Photo uploaded successfully!');
    resetForm();
    
    const modal = document.getElementById('uploadModal');
    setTimeout(() => {
      modal.classList.remove('open');
    }, 2000);
    
  } catch (error) {
    console.error('[UPLOAD POST] Upload error:', error);
    showError('An error occurred during upload');
  } finally {
    showLoading(false);
  }
}

function resetForm() {
  const uploadForm = document.getElementById('uploadForm');
  const preview = document.getElementById('preview');
  
  uploadForm.reset();
  preview.innerHTML = '';
  hideMessages();
  showLoading(false);
  
  if (tagList) {
    tagList.set_items([]);
  }
  if (tagAutocomplete) {
    const searchInput = document.querySelector('.sa-input');
    if (searchInput) {
      searchInput.value = '';
    }
  }
}

function showToast(message, type = 'success') {
  const stack = document.getElementById('toastStack');
  if (!stack) return;

  const toast = document.createElement('div');
  toast.className = `toast toast--${type}`;
  toast.textContent = message;

  stack.appendChild(toast);

  setTimeout(() => {
    toast.remove();
  }, 3000);
}

function showError(message) {
  showToast(message, 'error');
}

function showSuccess(message) {
  showToast(message, 'success');
}


function hideMessages() {
  document.getElementById('errorMessage').classList.remove('show');
  document.getElementById('successMessage').classList.remove('show');
}

function showLoading(show) {
  const loading = document.getElementById('loading');
  if (show) {
    loading.classList.add('show');
  } else {
    loading.classList.remove('show');
  }
}
