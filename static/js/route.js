// TODO: API 또는 전체 데이터베이스에서 가져온 실제 역 목록으로 교체해야 합니다.
// 각 역 객체에는 고유 ID, 역명, 호선 목록, 좌표 등의 정보가 포함되어야 합니다.
// Mock data for stations
// const stations = [
//     { name: '강남역', lines: ['2호선', '분당선'] },
//     { name: '선릉역', lines: ['2호선', '분당선'] },
//     { name: '삼성역', lines: ['2호선'] },
//     { name: '신도림역', lines: ['2호선', '1호선'] },
//     { name: '여의도역', lines: ['5호선', '9호선'] },
//     { name: '여의나루역', lines: ['5호선', '9호선'] },
//     { name: '시청역', lines: ['1호선', '2호선'] },
//     { name: '종각역', lines: ['1호선', '3호선'] },
//     { name: '홍대입구역', lines: ['2호선', '6호선', '경의중앙선'] },
//     { name: '합정역', lines: ['2호선', '6호선'] }
// ];

// Current route state
// let currentStep = 1;
// let totalSteps = 5;
// let currentRoute = null;

// Initialize the app
document.addEventListener('DOMContentLoaded', function() {
    initializeRoutePage();
});

function initializeRoutePage() {
    setupStationInputs();
    console.log('길찾기 페이지가 로드되었습니다.');
}

// 역 입력 시 자동완성 기능
function setupStationInputs() {
    const startInput = document.getElementById('startStation');
    const endInput = document.getElementById('endStation');

    setupAutocomplete(startInput, 'startSuggestions');
    setupAutocomplete(endInput, 'endSuggestions');
}

function setupAutocomplete(input, suggestionsId) {
    const suggestionsContainer = document.getElementById(suggestionsId);

    // Use event delegation for suggestion clicks
    suggestionsContainer.addEventListener('mousedown', function(e) {
        if (e.target && e.target.matches('div.suggestion-item')) {
            selectStation(e.target.dataset.stationName, input.id);
        }
    });

    // debounce와 fetchStations 사용
    input.addEventListener('input', debounce(async function() { // <--- 1. debounce 적용
        const value = this.value;
        suggestionsContainer.innerHTML = ''; // 이전 제안 삭제

        if (value.length < 1) {
            suggestionsContainer.style.display = 'none';
            return;
        }

        // 2. API 호출로 stations 데이터를 가져옴 (search-util.js의 함수 사용)
        const stations = await fetchStations(value);

        if (stations.length > 0) {
            stations.forEach(station => {
                const div = document.createElement('div');
                div.className = 'suggestion-item';
                // 3. API 응답 구조에 맞게 수정 (station.line이 있는지 확인)
                div.innerHTML = station.line 
                                ? `${station.name} (${station.line})` 
                                : station.name;
                div.dataset.stationName = station.name;
                suggestionsContainer.appendChild(div);
            });
            suggestionsContainer.style.display = 'block';
        } else {
            suggestionsContainer.style.display = 'none';
        }
    }, 300)); // 300ms 지연

    input.addEventListener('blur', function() {
        // Use a short delay to allow click events on suggestions to fire
        setTimeout(() => {
            suggestionsContainer.style.display = 'none';
        }, 200);
    });
}

function selectStation(stationName, inputId) {
    const input = document.getElementById(inputId);
    const suggestions = document.getElementById(inputId.replace('Station', 'Suggestions'));

    input.value = stationName;
    suggestions.style.display = 'none';
}

// '길찾기 시작' 버튼 -> 경로 찾기
// function startRouteSearch() {
//     const startStationName = document.getElementById('startStation').value;
//     const endStationName = document.getElementById('endStation').value;

//     if (!startStationName || !endStationName) {
//         alert('출발역과 도착역을 모두 입력해주세요.');
//         return;
//     }

//     if (startStationName === endStationName) {
//         alert('출발역과 도착역이 같을 수 없습니다.');
//         return;
//     }

//     const searchBtn = document.querySelector('.search-btn');
//     searchBtn.disabled = true;
//     searchBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 경로 탐색 중...';

//     setTimeout(() => {
//         document.getElementById('inputSection').style.display = 'none';

//         // TODO: API 또는 전체 데이터베이스에서 가져온 실제 역 목록으로 교체해야 합니다.
//         // 각 역 객체에는 역명, 호선 목록, 소요 시간 등의 정보가 포함되어야 합니다.
//         // --- Set Marker Colors and Names ---
//         const startStation = stations.find(s => s.name === startStationName) || { lines: ['2호선'] };
//         const endStation = stations.find(s => s.name === endStationName) || { lines: ['3호선'] };
//         const transferStation = stations.find(s => s.name === '선릉역') || { lines: ['분당선'] };

//         document.getElementById('startStationName').textContent = startStationName;
//         document.getElementById('endStationName').textContent = endStationName;
//         document.getElementById('transferStationName').textContent = '선릉';

//         const startMarker = document.querySelector('.station-marker.start');
//         const endMarker = document.querySelector('.station-marker.end');
//         const transferMarker = document.getElementById('transferMarker');

//         startMarker.className = 'station-marker start '; // Reset classes
//         endMarker.className = 'station-marker end ';
//         transferMarker.className = 'transfer-marker ';

//         startMarker.classList.add(getLineClass(startStation.lines[0]));
//         endMarker.classList.add(getLineClass(endStation.lines[0]));
//         transferMarker.classList.add(getLineClass(transferStation.lines[0]));
//         // --- End of Marker Color Logic ---

//         document.getElementById('routeGuidance').style.display = 'block';

//         currentRoute = {
//             start: startStationName,
//             end: endStationName,
//             steps: generateRouteSteps(startStationName, endStationName)
//         };
//         totalSteps = currentRoute.steps.length;

//         updateRouteStep();

//         searchBtn.disabled = false;
//         searchBtn.innerHTML = '<i class="fas fa-search"></i> 길찾기 시작';
//     }, 1500);
// }

// function getIcon(iconKeyword) {
//     const iconMap = {
//         'subway': 'fa-subway',
//         'walk': 'fa-walking',
//         'escalator': 'fa-arrow-up', // Changed icon
//         'stairs': 'fa-walking', // Using fa-walking as a stand-in
//         'exit': 'fa-door-open',
//         'arrive': 'fa-flag-checkered',
//         'transfer': 'fa-exchange-alt'
//     };
//     return iconMap[iconKeyword] || 'fa-question-circle';
// }

// TODO: 실제 길찾기 API를 호출하고 그 결과를 파싱하여 경로 단계를 생성하는 로직으로 대체해야 합니다.
// API는 출발지, 도착지, 사용자 설정(최단 시간, 최소 환승 등)을 인자로 받아야 합니다.
// 현재는 고정된 모의 경로를 반환합니다.
// function generateRouteSteps(start, end) {
//     // Mock route steps with realistic subway guidance and icons
//     return [
//         {
//             instruction: [`<span class="highlight">${start}</span>`, '승강장으로 이동하세요'],
//             position: 'start',
//             times: ['2분', '5분'],
//             icon: 'walk',
//             line: '2호선' // Added line property
//         },
//         {
//             instruction: ['<span class="highlight">2호선</span> 승차 후', '3개 역 이동'],
//             position: 'start',
//             times: ['2분', '5분'],
//             icon: 'subway',
//             line: '2호선'
//         },
//         {
//             instruction: ['<span class="highlight">선릉역</span>에서 하차', '환승 통로로 이동'],
//             position: 'transfer',
//             times: ['2분', '5분'],
//             icon: 'walk',
//             line: '2호선'
//         },
//         {
//             instruction: ['<span class="highlight">분당선</span>으로 환승', '<span class="highlight">수원</span> 방향'],
//             position: 'transfer',
//             times: ['2분', '5분'],
//             icon: 'transfer',
//             line: '분당선' // Changed line
//         },
//         {
//             instruction: [`<span class="highlight">${end}</span>에서 하차`, '<span class="highlight">3번 출구</span>로 이동'],
//             position: 'end',
//             times: ['2분', '5분'],
//             icon: 'walk',
//             line: '분당선'
//         },
//         {
//             instruction: [`<span class="highlight">에스컬레이터</span>를 타고`, '지상으로 올라가세요'], // Highlighted text
//             position: 'end',
//             times: ['1분', '0분'],
//             icon: 'escalator',
//             line: '분당선'
//         },
//         {
//             instruction: ['목적지에', '도착했습니다!'],
//             position: 'end',
//             times: ['0분', '0분'],
//             icon: 'arrive',
//             line: '분당선'
//         }
//     ];
// }

// 경로 안내 카드
// function nextStep() {
//     if (currentStep < totalSteps) {
//         currentStep++;
//         updateRouteStep();
//     }
// }

// function previousStep() {
//     if (currentStep > 1) {
//         currentStep--;
//         updateRouteStep();
//     }
// }

// 경로 안내 시 위치 안내 헤더(route-progress)
function updateRouteStep() {
    if (!currentRoute) return;

    const step = currentRoute.steps[currentStep - 1];

    // Update instruction icon
    const instructionIcon = document.getElementById('instructionIcon').querySelector('i');
    instructionIcon.className = `fas ${getIcon(step.icon)}`;

    // Update instruction text
    const instructionText = document.getElementById('instructionText');
    instructionText.innerHTML = step.instruction.map(line =>
        `<div class="instruction-line">${line}</div>`
    ).join('');

    // Update time labels (2 segments only)
    document.getElementById('startTime').textContent = step.times[0];
    document.getElementById('endTime').textContent = step.times[1];

    // Update progress bar color based on line
    const progressBar = document.querySelector('.progress-line');
    const lineClass = getLineClass(step.line);

    // Remove old line classes from progress bar only
    progressBar.className = 'progress-line';
    if (lineClass) {
        progressBar.classList.add(lineClass);
    }

    // Show/hide transfer marker
    const transferMarker = document.getElementById('transferMarker');

    if (step.position === 'transfer') {
        transferMarker.style.display = 'flex';
    } else {
        transferMarker.style.display = 'none';
    }

    // Update train position based on step position (centered on markers)
    const trainIcon = document.getElementById('trainIcon');
    let trainPosition;

    switch(step.position) {
        case 'start':
            trainPosition = '10%';
            break;
        case 'transfer':
            trainPosition = '50%';
            break;
        case 'end':
            trainPosition = '90%';
            break;
        default:
            trainPosition = '10%';
    }

    trainIcon.style.left = trainPosition;

    // Update buttons
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');

    prevBtn.style.display = currentStep > 1 ? 'flex' : 'none';

    if (currentStep === totalSteps) {
        nextBtn.innerHTML = '<span>완료</span>';
        nextBtn.onclick = endGuidance;
    } else {
        nextBtn.innerHTML = '<span>다음</span>';
        nextBtn.onclick = nextStep;
    }
}

function updateRouteVisual(stations) {
    const stationLine = document.getElementById('stationLine');
    stationLine.innerHTML = '';

    stations.forEach((station, index) => {
        // Add station
        const stationEl = document.createElement('div');
        stationEl.className = 'station';
        if (index === 0) stationEl.classList.add('current');
        stationEl.textContent = station;
        stationLine.appendChild(stationEl);

        // Add line segment (except for last station)
        if (index < stations.length - 1) {
            const segment = document.createElement('div');
            segment.className = 'line-segment';
            segment.innerHTML = `
                <div class="line"></div>
                <span class="time">${Math.floor(Math.random() * 5) + 2}분</span>
            `;
            stationLine.appendChild(segment);
        }
    });
}

// function endGuidance() {
//     alert('경로 안내가 종료되었습니다.');

//     // Show input section again
//     document.getElementById('inputSection').style.display = 'block';
//     document.getElementById('routeGuidance').style.display = 'none';

//     // Reset state
//     currentStep = 1;
//     currentRoute = null;

//     // Reset form
//     document.getElementById('startStation').value = '';
//     document.getElementById('endStation').value = '';

//     // Scroll to top
//     window.scrollTo({ top: 0, behavior: 'smooth' });
// }

// Audio functions
// function playAudio() {
//     const instructionLines = document.querySelectorAll('.instruction-line');
//     const instruction = Array.from(instructionLines).map(line => line.textContent).join(' ');

//     // Mock audio playback
//     console.log('Playing audio:', instruction);

//     // Show audio feedback
//     const btn = event.target.closest('.action-btn');
//     const originalText = btn.innerHTML;
//     btn.innerHTML = '<i class="fas fa-volume-up"></i><span>재생 중...</span>';
//     btn.disabled = true;

//     setTimeout(() => {
//         btn.innerHTML = originalText;
//         btn.disabled = false;
//     }, 2000);
// }

// '편의 시설' 버튼 -> 출발역/환승역/도착역의 시설 정보(모달)
function showFacilities() {
    document.getElementById('facilitiesModal').classList.add('show');
}

function closeFacilitiesModal() {
    document.getElementById('facilitiesModal').classList.remove('show');
}

function selectFacilityStation(stationName) {
    // Update active button
    document.querySelectorAll('.station-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');

    // TODO: API 또는 전체 데이터베이스에서 가져온 실제 역 목록으로 교체해야 합니다.
    // 각 역 객체에는 고유 ID, 역명, 편의 시설 등의 정보가 포함되어야 합니다.
    // Update facility details
    const details = document.getElementById('facilityDetails');
    const stationNames = {
        'gangnam': '강남역',
        'seolleung': '선릉역',
        'samsung': '삼성역'
    };

    details.innerHTML = `
        <h4>${stationNames[stationName]} 편의시설</h4>
        <div class="facility-list">
            <div class="facility-item">
                <i class="fas fa-walking"></i>
                <span>에스컬레이터: 1,2,3,4번 출구</span>
            </div>
            <div class="facility-item">
                <i class="fas fa-wheelchair"></i>
                <span>엘리베이터: 2,4번 출구</span>
            </div>
            <div class="facility-item">
                <i class="fas fa-restroom"></i>
                <span>화장실: 1,3번 출구 근처</span>
            </div>
        </div>
    `;
}

// '이용 불가' 버튼 -> 임시 알림창
function reportClosure() {
    // '아직 구현되지 않은 기능입니다.' 라는 알림창을 띄웁니다.
    alert('아직 구현되지 않은 기능입니다.');
}

// // '이용 불가' 버튼 -> 대체 경로 안내
// function reportClosure() {
//     if (confirm('현재 경로에서 문제가 발생했나요? 대체 경로를 안내해드리겠습니다.')) {
//         alert('죄송합니다. 빠른 대체 경로를 안내합니다');

//         // Mock alternative route
//         setTimeout(() => {
//             currentStep = 1;
//             currentRoute.steps = generateAlternativeRoute();
//             updateRouteStep();
//         }, 2000);
//     }
// }

// function generateAlternativeRoute() {
//     // TODO: 실제 길찾기 API를 호출하고 그 결과를 파싱하여 경로 단계를 생성하는 로직으로 대체해야 합니다.
//     // API는 출발지, 도착지, 사용자 설정(최단 시간, 최소 환승 등)을 인자로 받아야 합니다.
//     // 차순위 경로 또는 장애물 회피 경로를 반환해야 합니다.
//     // 현재는 고정된 모의 경로를 반환합니다.
//     return [
//         {
//             instruction: '대체 경로로 안내합니다',
//             detail: '에스컬레이터 이용이 어려우시군요. 엘리베이터를 이용한 경로로 안내해드립니다.',
//             stations: [currentRoute.start, '선릉', '삼성', currentRoute.end]
//         },
//         {
//             instruction: '엘리베이터를 이용하세요',
//             detail: '2번 출구 엘리베이터를 이용하여 승강장으로 이동하세요.',
//             stations: ['선릉']
//         },
//         {
//             instruction: '목적지에 도착했습니다',
//             detail: '안전한 여행 되세요!',
//             stations: [currentRoute.end]
//         }
//     ];
// }

// Navigation
// const appContainer = document.getElementById('wisheasy-app');

// function goBack() {
//     const routeGuidance = document.getElementById('routeGuidance');
//     // 경로 안내 카드가 화면에 표시된 상태라면, 경로 안내 카드를 숨기고 다시 검색 화면으로 이동
//     if (routeGuidance.style.display === 'block') {
//         routeGuidance.style.display = 'none';
//         document.querySelector('.input-section').style.display = 'block';
//         document.getElementById('startStation').value = ''
//         document.getElementById('endStation').value = ''
//     }
//     // 방문 기록이 있으면서, 동시에 외부 페이지를 통해 정상적으로 들어온 경우에만 뒤로가기
//     else if (window.history.length > 1 && document.referrer) {
//         window.history.back();
//     }
//     // 그렇지 않다면, 메인 페이지로 이동
//     else {
//         const mainPageUrl = appContainer.dataset.mainPageUrl;
//         window.location.href = mainPageUrl;
//     }
// }

// Close modals when clicking outside
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal')) {
        e.target.classList.remove('show');
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Escape key to go back or close modals
    if (e.key === 'Escape') {
        const openModal = document.querySelector('.modal.show');
        if (openModal) {
            openModal.classList.remove('show');
        } else {
            goBack();
        }
    }

    // Route navigation shortcuts
    if (document.getElementById('routeGuidance').style.display !== 'none') {
        if (e.key === 'ArrowLeft') {
            previousStep();
        } else if (e.key === 'ArrowRight') {
            nextStep();
        }
    }
});
