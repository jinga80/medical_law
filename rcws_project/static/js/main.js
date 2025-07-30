// Main JavaScript for RCWS

$(document).ready(function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Initialize dropdowns properly
    var dropdownElementList = [].slice.call(document.querySelectorAll('.dropdown-toggle'));
    var dropdownList = dropdownElementList.map(function (dropdownToggleEl) {
        return new bootstrap.Dropdown(dropdownToggleEl);
    });

    // Fix user dropdown menu
    $('#userDropdown').on('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        var $dropdown = $(this).next('.dropdown-menu');
        $dropdown.toggleClass('show');
        $(this).attr('aria-expanded', $dropdown.hasClass('show'));
    });

    // Close dropdown when clicking outside
    $(document).on('click', function(e) {
        if (!$(e.target).closest('.dropdown').length) {
            $('.dropdown-menu').removeClass('show');
            $('.dropdown-toggle').attr('aria-expanded', 'false');
        }
    });

    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        $('.alert').fadeOut('slow');
    }, 5000);

    // Confirm delete actions
    $('.delete-confirm').on('click', function(e) {
        if (!confirm('정말로 삭제하시겠습니까?')) {
            e.preventDefault();
        }
    });

    // Form validation
    $('form').on('submit', function() {
        var $form = $(this);
        var $submitBtn = $form.find('button[type="submit"]');
        
        if ($form[0].checkValidity()) {
            $submitBtn.prop('disabled', true);
            $submitBtn.html('<span class="spinner-border spinner-border-sm me-2"></span>처리 중...');
        }
    });

    // Table row selection
    $('.table tbody tr').on('click', function() {
        $(this).toggleClass('table-active');
    });

    // Search functionality
    $('.search-input').on('keyup', function() {
        var value = $(this).val().toLowerCase();
        $('.table tbody tr').filter(function() {
            $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1);
        });
    });

    // Sortable tables
    $('.sortable').on('click', function() {
        var table = $(this).closest('table');
        var index = $(this).index();
        var rows = table.find('tbody tr').get();
        
        rows.sort(function(a, b) {
            var A = $(a).children('td').eq(index).text().toUpperCase();
            var B = $(b).children('td').eq(index).text().toUpperCase();
            
            if (A < B) return -1;
            if (A > B) return 1;
            return 0;
        });
        
        $.each(rows, function(index, row) {
            table.children('tbody').append(row);
        });
    });

    // Progress bar animation
    $('.progress-bar').each(function() {
        var $this = $(this);
        var percentage = $this.attr('aria-valuenow');
        $this.css('width', '0%').animate({
            width: percentage + '%'
        }, 1000);
    });

    // Modal events
    $('.modal').on('show.bs.modal', function() {
        var $modal = $(this);
        var $form = $modal.find('form');
        if ($form.length) {
            $form[0].reset();
        }
    });

    // File upload preview
    $('input[type="file"]').on('change', function() {
        var file = this.files[0];
        var $preview = $(this).siblings('.file-preview');
        
        if (file && file.type.startsWith('image/')) {
            var reader = new FileReader();
            reader.onload = function(e) {
                $preview.html('<img src="' + e.target.result + '" class="img-thumbnail" style="max-width: 200px;">');
            };
            reader.readAsDataURL(file);
        } else {
            $preview.html('<p class="text-muted">' + file.name + '</p>');
        }
    });

    // Date picker initialization
    $('input[type="date"]').each(function() {
        if (!$(this).val()) {
            $(this).val(new Date().toISOString().split('T')[0]);
        }
    });

    // Auto-save forms
    var autoSaveTimer;
    $('form textarea, form input[type="text"]').on('input', function() {
        clearTimeout(autoSaveTimer);
        autoSaveTimer = setTimeout(function() {
            // Auto-save logic here
            console.log('Auto-saving...');
        }, 2000);
    });

    // Notification handling
    function showNotification(title, message, type = 'info') {
        var alertClass = 'alert-' + type;
        var alertHtml = `
            <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
                <strong>${title}</strong> ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        $('.container-fluid').first().prepend(alertHtml);
        
        setTimeout(function() {
            $('.alert').first().fadeOut('slow');
        }, 5000);
    }

    // Global notification function
    window.showNotification = showNotification;

    // AJAX error handling
    $(document).ajaxError(function(event, xhr, settings, error) {
        console.error('AJAX Error:', error);
        showNotification('오류', '요청 처리 중 오류가 발생했습니다.', 'danger');
    });

    // Loading states
    function setLoadingState($element, loading = true) {
        if (loading) {
            $element.prop('disabled', true);
            $element.data('original-text', $element.text());
            $element.html('<span class="spinner-border spinner-border-sm me-2"></span>처리 중...');
        } else {
            $element.prop('disabled', false);
            $element.text($element.data('original-text'));
        }
    }

    // Global loading function
    window.setLoadingState = setLoadingState;

    // Responsive table
    function makeTableResponsive() {
        $('.table-responsive').each(function() {
            var $table = $(this);
            var $tableElement = $table.find('table');
            
            if ($tableElement.width() > $table.width()) {
                $table.addClass('table-scroll');
            }
        });
    }

    // Call on load and resize
    makeTableResponsive();
    $(window).on('resize', makeTableResponsive);

    // 현재 시간 표시 (base.html의 JavaScript와 중복 방지)
    function updateCurrentTime() {
        // base.html에서 이미 처리하고 있으므로 여기서는 비활성화
        return;
        
        const now = new Date();
        const timeString = now.toLocaleTimeString('ko-KR', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        });
        const dateString = now.toLocaleDateString('ko-KR', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            weekday: 'long'
        });
        
        const timeElement = document.getElementById('current-time');
        if (timeElement) {
            timeElement.innerHTML = `
                <div class="d-flex align-items-center">
                    <i class="mdi mdi-clock me-2"></i>
                    <span>${timeString}</span>
                </div>
                <small class="text-white-50">${dateString}</small>
            `;
        }
    }

    // 시간 업데이트 시작 (base.html에서 처리하므로 비활성화)
    // updateCurrentTime();
    // setInterval(updateCurrentTime, 1000);

    // Keyboard shortcuts
    $(document).on('keydown', function(e) {
        // Ctrl/Cmd + S for save
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            $('form:visible button[type="submit"]').first().click();
        }
        
        // Escape to close modals
        if (e.key === 'Escape') {
            $('.modal').modal('hide');
        }
    });

    // Infinite scroll for tables
    var page = 1;
    var loading = false;
    
    $(window).on('scroll', function() {
        if ($(window).scrollTop() + $(window).height() >= $(document).height() - 100) {
            if (!loading && $('.pagination').length) {
                loadMoreData();
            }
        }
    });

    function loadMoreData() {
        loading = true;
        page++;
        
        $.ajax({
            url: window.location.pathname,
            data: { page: page },
            success: function(data) {
                // Append new data to table
                $('.table tbody').append(data);
                loading = false;
            },
            error: function() {
                loading = false;
            }
        });
    }

    // Chart.js configuration
    if (typeof Chart !== 'undefined') {
        Chart.defaults.font.family = "'Noto Sans KR', sans-serif";
        Chart.defaults.color = '#6c757d';
        Chart.defaults.plugins.legend.labels.usePointStyle = true;
    }

    // Print functionality
    $('.print-btn').on('click', function() {
        window.print();
    });

    // Export functionality
    $('.export-btn').on('click', function() {
        var format = $(this).data('format');
        var table = $(this).closest('.card').find('table');
        
        if (format === 'csv') {
            exportTableToCSV(table);
        } else if (format === 'excel') {
            exportTableToExcel(table);
        }
    });

    function exportTableToCSV($table) {
        var csv = [];
        var rows = $table.find('tr');
        
        for (var i = 0; i < rows.length; i++) {
            var row = [], cols = rows[i].querySelectorAll('td, th');
            
            for (var j = 0; j < cols.length; j++) {
                var text = cols[j].innerText.replace(/"/g, '""');
                row.push('"' + text + '"');
            }
            
            csv.push(row.join(','));
        }
        
        downloadCSV(csv.join('\n'), 'export.csv');
    }

    function downloadCSV(csv, filename) {
        var blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        var link = document.createElement('a');
        
        if (link.download !== undefined) {
            var url = URL.createObjectURL(blob);
            link.setAttribute('href', url);
            link.setAttribute('download', filename);
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    }

    // Theme switcher
    $('.theme-switcher').on('click', function() {
        var currentTheme = $('body').attr('data-theme') || 'light';
        var newTheme = currentTheme === 'light' ? 'dark' : 'light';
        
        $('body').attr('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        
        // Update UI elements
        if (newTheme === 'dark') {
            $('body').addClass('dark-theme');
        } else {
            $('body').removeClass('dark-theme');
        }
    });

    // Load saved theme
    var savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        $('body').attr('data-theme', savedTheme);
        if (savedTheme === 'dark') {
            $('body').addClass('dark-theme');
        }
    }

    // 알림 드롭다운 토글
    const notificationDropdown = document.getElementById('notificationsDropdown');
    if (notificationDropdown) {
        notificationDropdown.addEventListener('click', function(e) {
            e.preventDefault();
            const dropdownMenu = this.nextElementSibling;
            dropdownMenu.classList.toggle('show');
        });
    }

    // 사용자 메뉴 드롭다운 토글
    const userDropdown = document.getElementById('userDropdown');
    if (userDropdown) {
        userDropdown.addEventListener('click', function(e) {
            e.preventDefault();
            const dropdownMenu = this.nextElementSibling;
            dropdownMenu.classList.toggle('show');
        });
    }

    // 알림 읽음 처리
    const markAsReadButtons = document.querySelectorAll('.mark-as-read');
    markAsReadButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const notificationId = this.dataset.notificationId;
            markNotificationAsRead(notificationId, this);
        });
    });

    // 모든 알림 읽음 처리
    const markAllAsReadButton = document.getElementById('markAllAsRead');
    if (markAllAsReadButton) {
        markAllAsReadButton.addEventListener('click', function(e) {
            e.preventDefault();
            markAllNotificationsAsRead();
        });
    }

    // 폼 유효성 검사
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // 실시간 검색
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                performSearch(this.value);
            }, 300);
        });
    }

    // 모달 자동 숨김
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.addEventListener('hidden.bs.modal', function() {
            // 모달이 닫힐 때 폼 리셋
            const form = this.querySelector('form');
            if (form) {
                form.reset();
                form.classList.remove('was-validated');
            }
        });
    });

    // 병원 선택 시 지점 목록 갱신 (채용 요청 생성 페이지에서만 작동)
    $(document).on('change', '#id_hospital', function() {
        // 채용 요청 생성 페이지가 아닌 경우에만 실행
        if (!window.location.pathname.includes('/workflow/job-requests/create/')) {
            const hospitalId = $(this).val();
            if (hospitalId) {
                axios.get('/accounts/api/hospitals/' + hospitalId + '/branches/')
                    .then(function(response) {
                        const branches = response.data;
                        if (branches && Array.isArray(branches)) {
                            let options = '<option value="">지점 선택</option>';
                            branches.forEach(function(branch) {
                                options += `<option value="${branch.id}">${branch.name}</option>`;
                            });
                            $('#id_branch').html(options);
                            // 자동입력 초기화
                            $('#id_hospital_branch').val('');
                            $('#id_hospital_address').val('');
                            $('#id_hospital_phone').val('');
                            $('#id_hospital_contact_person').val('');
                        }
                    })
                    .catch(function(error) {
                        console.error('지점 목록 가져오기 실패:', error);
                    });
            } else {
                $('#id_branch').html('<option value="">지점 선택</option>');
            }
        }
    });
    // 지점 선택 시 상세정보 자동입력 (채용 요청 생성 페이지에서만 작동)
    $(document).on('change', '#id_branch', function() {
        // 채용 요청 생성 페이지가 아닌 경우에만 실행
        if (!window.location.pathname.includes('/workflow/job-requests/create/')) {
            const branchId = $(this).val();
            if (branchId) {
                axios.get('/accounts/api/branches/' + branchId + '/')
                    .then(function(response) {
                        const branch = response.data;
                        if (branch && branch.hospital) {
                            $('#id_hospital_name').val(branch.hospital.name);
                            $('#id_hospital_branch').val(branch.name);
                            $('#id_hospital_address').val(branch.address);
                            $('#id_hospital_phone').val(branch.phone);
                            $('#id_hospital_contact_person').val(branch.manager_name);
                        }
                    })
                    .catch(function(error) {
                        console.error('지점 정보 가져오기 실패:', error);
                    });
            }
        }
    });
    // 포지션 템플릿 선택 시 채용정보 자동입력 (채용 요청 생성 페이지에서만 작동)
    $(document).on('change', '#id_position_template', function() {
        // 채용 요청 생성 페이지가 아닌 경우에만 실행
        if (!window.location.pathname.includes('/workflow/job-requests/create/')) {
            const posId = $(this).val();
            if (posId) {
                axios.get('/accounts/api/positions/' + posId + '/')
                    .then(function(response) {
                        const template = response.data;
                        if (template) {
                            $('#id_position_title').val(template.title);
                            $('#id_department').val(template.department);
                            $('#id_employment_type').val(template.employment_type);
                            $('#id_salary_min').val(template.salary_min);
                            $('#id_salary_max').val(template.salary_max);
                            $('#id_required_experience').val(template.required_experience);
                            $('#id_preferred_qualifications').val(template.preferred_qualifications);
                            $('#id_job_description').val(template.job_description);
                            $('#id_working_hours').val(template.working_hours);
                            $('#id_working_location').val(template.working_location);
                            $('#id_special_requirements').val(template.special_requirements);
                            $('#id_recruitment_period').val(template.recruitment_period);
                            $('#id_urgency_level').val(template.urgency_level);
                        }
                    })
                    .catch(function(error) {
                        console.error('포지션 템플릿 정보 가져오기 실패:', error);
                    });
            }
        }
    });
});

// Utility functions
function formatDate(date) {
    return new Date(date).toLocaleDateString('ko-KR');
}

function formatDateTime(date) {
    return new Date(date).toLocaleString('ko-KR');
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('ko-KR', {
        style: 'currency',
        currency: 'KRW'
    }).format(amount);
}

function debounce(func, wait) {
    var timeout;
    return function executedFunction() {
        var later = function() {
            clearTimeout(timeout);
            func();
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    var inThrottle;
    return function() {
        var args = arguments;
        var context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(function() {
                inThrottle = false;
            }, limit);
        }
    };
}

// 알림 읽음 처리 함수
function markNotificationAsRead(notificationId, button) {
    fetch(`/dashboard/notifications/${notificationId}/read/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            button.closest('.notification-item').classList.remove('unread');
            updateNotificationCount();
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// 모든 알림 읽음 처리 함수
function markAllNotificationsAsRead() {
    fetch('/dashboard/notifications/read-all/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.querySelectorAll('.notification-item.unread').forEach(item => {
                item.classList.remove('unread');
            });
            updateNotificationCount();
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// 알림 개수 업데이트
function updateNotificationCount() {
    const badge = document.querySelector('.badge');
    if (badge) {
        const unreadCount = document.querySelectorAll('.notification-item.unread').length;
        if (unreadCount === 0) {
            badge.style.display = 'none';
        } else {
            badge.style.display = 'inline';
            badge.textContent = unreadCount;
        }
    }
}

// 실시간 검색 함수
function performSearch(query) {
    const searchResults = document.getElementById('searchResults');
    if (!searchResults) return;

    if (query.length < 2) {
        searchResults.innerHTML = '';
        return;
    }

    fetch(`/api/search/?q=${encodeURIComponent(query)}`, {
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
        },
    })
    .then(response => response.json())
    .then(data => {
        displaySearchResults(data.results);
    })
    .catch(error => {
        console.error('Search error:', error);
    });
}

// 검색 결과 표시
function displaySearchResults(results) {
    const searchResults = document.getElementById('searchResults');
    if (!searchResults) return;

    if (results.length === 0) {
        searchResults.innerHTML = '<div class="p-3 text-muted">검색 결과가 없습니다.</div>';
        return;
    }

    const html = results.map(result => `
        <a href="${result.url}" class="dropdown-item">
            <div class="d-flex align-items-center">
                <i class="mdi mdi-${result.icon} me-2"></i>
                <div>
                    <div class="fw-bold">${result.title}</div>
                    <small class="text-muted">${result.description}</small>
                </div>
            </div>
        </a>
    `).join('');

    searchResults.innerHTML = html;
}

// CSRF 토큰 가져오기
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// 토스트 메시지 표시
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1055';
        document.body.appendChild(container);
    }

    const toastId = 'toast-' + Date.now();
    const toastHtml = `
        <div id="${toastId}" class="toast" role="alert">
            <div class="toast-header">
                <strong class="me-auto">알림</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;

    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement);
    toast.show();

    // 5초 후 자동 제거
    setTimeout(() => {
        if (toastElement.parentNode) {
            toastElement.parentNode.removeChild(toastElement);
        }
    }, 5000);
}

// 페이지 로딩 스피너
function showLoading() {
    const spinner = document.createElement('div');
    spinner.id = 'loadingSpinner';
    spinner.className = 'position-fixed top-0 start-0 w-100 h-100 d-flex justify-content-center align-items-center';
    spinner.style.backgroundColor = 'rgba(0,0,0,0.5)';
    spinner.style.zIndex = '9999';
    spinner.innerHTML = `
        <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">로딩 중...</span>
        </div>
    `;
    document.body.appendChild(spinner);
}

function hideLoading() {
    const spinner = document.getElementById('loadingSpinner');
    if (spinner) {
        spinner.remove();
    }
}

// 전역 함수로 노출
window.showToast = showToast;
window.showLoading = showLoading;
window.hideLoading = hideLoading; 