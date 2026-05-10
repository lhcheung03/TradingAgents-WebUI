const { createApp, ref, computed, onMounted, onUnmounted, watch } = Vue;

const AGENTS = [
    "Market Analyst",
    "Sentiment Analyst", 
    "News Analyst",
    "Fundamentals Analyst",
    "Bull Researcher",
    "Bear Researcher",
    "Research Manager",
    "Aggressive Analyst",
    "Neutral Analyst",
    "Conservative Analyst",
    "Trader",
    "Portfolio Manager"
];

const app = createApp({
    setup() {
        const config = ref({
            ticker: "NVDA",
            date: new Date().toISOString().split('T')[0],
            provider: "openai",
            model: "gpt-5.4-mini",
            max_debate_rounds: 1
        });

        const providers = ref([]);
        const models = ref({});
        const currentModels = ref([]);
        const apiKeysConfigured = ref({});
        
        const isRunning = ref(false);
        const currentRunId = ref(null);
        const currentStatus = ref("idle");
        const progress = ref(0);
        const messages = ref([]);
        const agentStates = ref({});
        const errorMessage = ref(null);
        
        const reports = ref([]);
        const selectedReport = ref(null);
        const memoryEntries = ref([]);
        
        const ws = ref(null);
        const wsReconnect = ref(null);
        
        // Stats tracking
        const llmCalls = ref(0);
        const toolCalls = ref(0);
        const tokensIn = ref(0);
        const tokensOut = ref(0);
        const elapsedTime = ref("00:00");
        const totalAgents = ref(12);
        const completedAgents = ref(0);
        let statsInterval = null;
        let startTime = null;
        
        const lastMessage = computed(() => {
            if (messages.value.length === 0) return "";
            return messages.value[messages.value.length - 1].message;
        });
        
        const providerApiKeyMissing = computed(() => {
            const p = config.value.provider;
            return p && apiKeysConfigured.value[p] === false;
        });
        
        const renderedReport = computed(() => {
            if (!selectedReport.value || !selectedReport.value.content) return "";
            return marked.parse(selectedReport.value.content);
        });

        async function loadConfig() {
            try {
                const res = await fetch('/api/config');
                const data = await res.json();
                providers.value = data.providers;
                models.value = data.models;
                apiKeysConfigured.value = data.api_keys_configured || {};
                
                if (providers.value.length > 0) {
                    config.value.provider = providers.value[0].key;
                }
                updateModelList();
            } catch (e) {
                console.error("Failed to load config:", e);
            }
        }

        function updateModelList() {
            const providerModels = models.value[config.value.provider];
            if (providerModels && providerModels.quick) {
                currentModels.value = providerModels.quick;
                if (providerModels.quick.length > 0) {
                    config.value.model = providerModels.quick[0][1];
                }
            }
        }

        function onProviderChange() {
            updateModelList();
        }

        async function loadReports() {
            try {
                const res = await fetch('/api/reports');
                const data = await res.json();
                reports.value = data.reports || [];
            } catch (e) {
                console.error("Failed to load reports:", e);
            }
        }

        async function loadReport(reportId) {
            try {
                const res = await fetch(`/api/reports/${reportId}`);
                const data = await res.json();
                selectedReport.value = data;
            } catch (e) {
                console.error("Failed to load report:", e);
            }
        }

        async function loadMemory() {
            try {
                const res = await fetch('/api/memory');
                const data = await res.json();
                memoryEntries.value = data.entries || [];
            } catch (e) {
                console.error("Failed to load memory:", e);
            }
        }

        async function startAnalysis() {
            if (!config.value.ticker || isRunning.value) return;
            
            errorMessage.value = null;
            isRunning.value = true;
            currentStatus.value = "starting";
            progress.value = 0;
            messages.value = [];
            agentStates.value = {};
            selectedReport.value = null;
            
            // Reset stats
            llmCalls.value = 0;
            toolCalls.value = 0;
            tokensIn.value = 0;
            tokensOut.value = 0;
            completedAgents.value = 0;
            startTime = Date.now();
            
            // Start elapsed time ticker
            if (statsInterval) clearInterval(statsInterval);
            statsInterval = setInterval(() => {
                const elapsed = Math.floor((Date.now() - startTime) / 1000);
                const mins = Math.floor(elapsed / 60);
                const secs = elapsed % 60;
                elapsedTime.value = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
            }, 1000);
            
            try {
                const res = await fetch('/api/start', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(config.value)
                });
                
                const data = await res.json();
                
                if (!res.ok) {
                    errorMessage.value = data.detail || `Server error: ${res.status}`;
                    isRunning.value = false;
                    if (statsInterval) clearInterval(statsInterval);
                    return;
                }
                
                currentRunId.value = data.run_id;
                
                connectWebSocket(data.run_id);
            } catch (e) {
                console.error("Failed to start analysis:", e);
                errorMessage.value = `Failed to connect: ${e.message}`;
                isRunning.value = false;
                if (statsInterval) clearInterval(statsInterval);
            }
        }

        function connectWebSocket(runId) {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/api/ws/${runId}`;
            
            ws.value = new WebSocket(wsUrl);
            
            ws.value.onopen = () => {
                console.log("WebSocket connected");
            };
            
            ws.value.onmessage = (event) => {
                const data = JSON.parse(event.data);
                handleWsMessage(data);
            };
            
            ws.value.onclose = () => {
                console.log("WebSocket disconnected");
                if (isRunning.value) {
                    wsReconnect.value = setTimeout(() => {
                        if (currentRunId.value) {
                            connectWebSocket(currentRunId.value);
                        }
                    }, 2000);
                }
            };
            
            ws.value.onerror = (e) => {
                console.error("WebSocket error:", e);
            };
        }

        function handleWsMessage(data) {
            // Update stats from message
            if (data.stats) {
                llmCalls.value = data.stats.llm_calls || llmCalls.value;
                toolCalls.value = data.stats.tool_calls || toolCalls.value;
                tokensIn.value = data.stats.tokens_in || tokensIn.value;
                tokensOut.value = data.stats.tokens_out || tokensOut.value;
            }
            
            switch (data.type) {
                case 'connected':
                case 'status_update':
                    currentStatus.value = data.status;
                    progress.value = data.progress || 0;
                    if (data.messages) {
                        messages.value = data.messages;
                    }
                    if (data.agent_states) {
                        agentStates.value = data.agent_states;
                        // Count completed agents
                        completedAgents.value = Object.values(data.agent_states).filter(s => s.state === 'completed').length;
                    }
                    break;
                    
                case 'agent_update':
                    if (data.agent_states) {
                        agentStates.value = data.agent_states;
                        completedAgents.value = Object.values(data.agent_states).filter(s => s.state === 'completed').length;
                    }
                    if (data.messages) {
                        messages.value = data.messages;
                    }
                    break;
                    
                case 'completed':
                    currentStatus.value = "completed";
                    progress.value = 100;
                    isRunning.value = false;
                    if (statsInterval) {
                        clearInterval(statsInterval);
                        statsInterval = null;
                    }
                    if (data.final_state) {
                        agentStates.value = data.agent_states || {};
                    }
                    loadReports();
                    if (data.report_id) {
                        loadReport(data.report_id);
                    }
                    break;
                    
                case 'error':
                    currentStatus.value = "failed";
                    isRunning.value = false;
                    errorMessage.value = data.error || "Analysis failed. Check API key and try again.";
                    if (data.messages) {
                        messages.value = data.messages;
                    }
                    if (statsInterval) {
                        clearInterval(statsInterval);
                        statsInterval = null;
                    }
                    console.error("Analysis error:", data.error);
                    break;
            }
        }

        function getAgentState(agent) {
            const state = agentStates.value[agent];
            return state ? state.state : 'idle';
        }

        function getAgentMessage(agent) {
            const state = agentStates.value[agent];
            return state ? (state.message || getStateDescription(state.state)) : getStateDescription('idle');
        }

        function getStateDescription(state) {
            const descriptions = {
                'idle': 'Waiting...',
                'running': 'Processing...',
                'completed': 'Done',
                'error': 'Error'
            };
            return descriptions[state] || state;
        }

        function getAgentDotClass(agent) {
            const state = getAgentState(agent);
            const classes = {
                'idle': 'bg-slate-500',
                'running': 'bg-blue-500 animate-pulse',
                'completed': 'bg-green-500',
                'error': 'bg-red-500'
            };
            return classes[state] || 'bg-slate-500';
        }

        function getAgentClass(agent) {
            const state = getAgentState(agent);
            const classes = {
                'idle': 'border-slate-700',
                'running': 'border-blue-500 bg-blue-500/10',
                'completed': 'border-green-500/50',
                'error': 'border-red-500 bg-red-500/10'
            };
            return classes[state] || 'border-slate-700';
        }

        function formatTime(timestamp) {
            if (!timestamp) return "";
            const date = new Date(timestamp);
            return date.toLocaleTimeString();
        }

function formatDate(dateStr) {
            if (!dateStr) return "";
            const date = new Date(dateStr);
            return date.toLocaleDateString() + " " + date.toLocaleTimeString();
        }
        
        function formatTokens(num) {
            if (num >= 1000) {
                return (num / 1000).toFixed(1) + 'k';
            }
            return num.toString();
        }
        
        function getCompletedAgentsCount() {
            return Object.values(agentStates.value).filter(s => s.state === 'completed').length;
        }
        
        onMounted(async () => {
            await loadConfig();
            await loadReports();
            await loadMemory();
        });

        onUnmounted(() => {
            if (ws.value) {
                ws.value.close();
            }
            if (wsReconnect.value) {
                clearTimeout(wsReconnect.value);
            }
        });

        watch(() => config.value.provider, () => {
            updateModelList();
        });

        return {
            config,
            providers,
            models,
            currentModels,
            apiKeysConfigured,
            isRunning,
            currentRunId,
            currentStatus,
            progress,
            messages,
            agentStates,
            errorMessage,
            reports,
            selectedReport,
            memoryEntries,
            lastMessage,
            providerApiKeyMissing,
            renderedReport,
            agents: AGENTS,
            llmCalls,
            toolCalls,
            tokensIn,
            tokensOut,
            elapsedTime,
            totalAgents,
            completedAgents,
            onProviderChange,
            startAnalysis,
            loadReport,
            loadMemory,
            getAgentState,
            getAgentMessage,
            getAgentDotClass,
            getAgentClass,
            formatTime,
            formatDate,
            formatTokens
        };
    }
});

app.mount('#app');