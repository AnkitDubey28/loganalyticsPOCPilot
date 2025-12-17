"""
Chat Assistant Agent - Conversational AI for log analysis and application guidance
Provides human-like NLP-based conversations about logs, errors, and application features
"""
import json
import re
from datetime import datetime, timedelta

class ChatAssistant:
    def __init__(self, ledger):
        self.ledger = ledger
        self.conversation_context = []
        
    def process_message(self, user_message):
        """Process user message with NLP-like understanding and generate conversational response"""
        message_lower = user_message.lower()
        
        # Store conversation context
        self.conversation_context.append({'user': user_message, 'timestamp': datetime.utcnow()})
        
        # Get current system state
        stats = self.ledger.get_stats()
        
        # Advanced intent detection with conversational patterns
        if self._is_greeting(message_lower):
            return self._greeting_response(stats)
        
        elif self._is_error_query(message_lower):
            return self._analyze_errors(message_lower)
        
        elif self._is_service_query(message_lower):
            return self._analyze_services(message_lower)
        
        elif self._is_time_based_query(message_lower):
            return self._analyze_time_based(message_lower)
        
        elif self._is_stats_query(message_lower):
            return self._show_comprehensive_stats(stats)
        
        elif self._is_search_help(message_lower):
            return self._help_search_logs()
        
        elif self._is_upload_help(message_lower):
            return self._help_upload_files()
        
        elif self._is_plugin_help(message_lower):
            return self._help_plugins()
        
        elif self._is_specific_log_search(message_lower):
            return self._search_specific_logs(message_lower)
        
        elif self._is_help_request(message_lower):
            return self._show_comprehensive_help()
        
        else:
            return self._intelligent_default_response(user_message, stats)
    
    # Intent detection methods
    def _is_greeting(self, msg):
        return any(word in msg for word in ['hi', 'hello', 'hey', 'good morning', 'good afternoon'])
    
    def _is_error_query(self, msg):
        return any(word in msg for word in ['error', 'errors', 'failed', 'failure', 'issue', 'problem', 'wrong', 'bug'])
    
    def _is_service_query(self, msg):
        return any(word in msg for word in ['service', 'services', 'which service', 'what service', 'microservice'])
    
    def _is_time_based_query(self, msg):
        return any(word in msg for word in ['recent', 'latest', 'last', 'today', 'yesterday', 'this week', 'past'])
    
    def _is_stats_query(self, msg):
        return any(word in msg for word in ['stats', 'statistics', 'overview', 'summary', 'status', 'how many', 'total'])
    
    def _is_search_help(self, msg):
        return any(phrase in msg for phrase in ['how to search', 'search logs', 'find logs', 'query logs'])
    
    def _is_upload_help(self, msg):
        return any(phrase in msg for phrase in ['upload', 'add file', 'ingest', 'import logs'])
    
    def _is_plugin_help(self, msg):
        return any(word in msg for word in ['plugin', 'fetch data', 'azure', 's3', 'api', 'webhook'])
    
    def _is_specific_log_search(self, msg):
        search_patterns = ['show me', 'give me', 'get me', 'find', 'search for', 'search', 'look for', 'display', 'list']
        # Check if any search pattern is followed by potential log-related terms
        for pattern in search_patterns:
            if pattern in msg:
                # Check if there are additional words after the pattern (indicating what to search)
                words_after = msg.split(pattern)[-1].strip().split()
                if len(words_after) > 0:
                    return True
        return False
    
    def _is_help_request(self, msg):
        return any(word in msg for word in ['help', 'guide', 'how', 'what can you', 'what do you'])
    
    # Response generators
    def _greeting_response(self, stats):
        total_events = stats.get('total_events', 0)
        if total_events > 0:
            return f"""
                Hey there! 👋 Great to see you!<br><br>
                
                I'm your LogSphere AI assistant, and I'm here to help you make sense of your log data. 
                I can see you've got <strong>{total_events:,} events</strong> in the system.<br><br>
                
                <strong>I can help you with:</strong><br>
                • 🔍 Finding and analyzing errors<br>
                • 📊 Understanding your log patterns<br>
                • 🎯 Searching for specific logs<br>
                • 📚 Navigating the application<br><br>
                
                What would you like to explore today?
            """
        else:
            return """
                Hey there! 👋 Welcome to LogSphere AI!<br><br>
                
                I'm your friendly log analysis assistant. I notice you haven't uploaded any logs yet, 
                but no worries - I can still help you get started!<br><br>
                
                <strong>Try asking me:</strong><br>
                • "How do I upload logs?"<br>
                • "What can you help me with?"<br>
                • "Tell me about plugins"<br><br>
                
                Ready to dive in? 🚀
            """
    
    def _analyze_errors(self, query):
        """Deep error analysis with conversational tone"""
        try:
            filters = {'level': 'ERROR'}
            error_events = self.ledger.list_events(filters=filters, limit=100)
            
            if not error_events:
                return """
                    ✨ <strong>Excellent news!</strong><br><br>
                    
                    I've scanned through all your logs and found <strong>zero errors</strong>. 
                    Your system is running smoothly! This is exactly what we like to see. 🎉<br><br>
                    
                    Keep monitoring though - I'll be here if anything comes up.
                """
            
            # Analyze error patterns
            error_services = {}
            error_messages = {}
            
            for event in error_events:
                service = event.get('service', 'Unknown')
                message = event.get('message', '')[:100]
                
                error_services[service] = error_services.get(service, 0) + 1
                error_messages[message] = error_messages.get(message, 0) + 1
            
            # Build conversational response
            response = f"<strong>🔴 Error Analysis Report</strong><br><br>"
            response += f"I found <strong>{len(error_events)} error events</strong> in your logs. "
            response += f"Let me break this down for you:<br><br>"
            
            # Service breakdown
            response += "<strong>📌 Errors by Service:</strong><br>"
            top_services = sorted(error_services.items(), key=lambda x: x[1], reverse=True)[:5]
            for service, count in top_services:
                percentage = (count / len(error_events)) * 100
                response += f"&nbsp;&nbsp;• <strong>{service}</strong>: {count} errors ({percentage:.1f}%)<br>"
            
            # Most common error
            if error_messages:
                top_error = sorted(error_messages.items(), key=lambda x: x[1], reverse=True)[0]
                response += f"<br><strong>🎯 Most Common Error:</strong><br>"
                response += f"<code style='font-size: 12px;'>{top_error[0]}</code><br>"
                response += f"<em>This appears {top_error[1]} times</em><br>"
            
            # Recommendations with links
            response += "<br><strong>💡 My Recommendations:</strong><br>"
            if len(top_services) > 0 and top_services[0][1] > len(error_events) * 0.5:
                response += f"&nbsp;&nbsp;• Focus on <strong>{top_services[0][0]}</strong> - it's generating most errors<br>"
            
            # Add link to search for errors
            error_search_url = "/search?level=ERROR"
            response += f"&nbsp;&nbsp;• <a href=\"{error_search_url}\" style=\"color: #667eea; font-weight: bold; text-decoration: none;\">🔗 View all errors in Search page →</a><br>"
            response += f"&nbsp;&nbsp;• <a href=\"/\" style=\"color: #667eea; font-weight: bold; text-decoration: none;\">📊 Check Dashboard for trends →</a><br>"
            
            return response
            
        except Exception as e:
            return f"I encountered an issue analyzing errors: {str(e)}. Let me know if you'd like to try again!"
    
    def _analyze_services(self, query):
        """Service activity analysis"""
        try:
            events = self.ledger.list_events(limit=1000)
            
            if not events:
                return """
                    I don't have any service data yet. Once you upload logs, 
                    I'll be able to show you which services are most active! 📊
                """
            
            services = {}
            service_levels = {}
            
            for event in events:
                service = event.get('service', 'Unknown')
                level = event.get('level', 'INFO')
                
                services[service] = services.get(service, 0) + 1
                
                if service not in service_levels:
                    service_levels[service] = {'ERROR': 0, 'WARN': 0, 'INFO': 0}
                service_levels[service][level] = service_levels[service].get(level, 0) + 1
            
            response = "<strong>⚙️ Service Activity Analysis</strong><br><br>"
            response += f"I'm tracking <strong>{len(services)} services</strong> across {len(events):,} events.<br><br>"
            
            response += "<strong>🏆 Top Services:</strong><br>"
            for service, count in sorted(services.items(), key=lambda x: x[1], reverse=True)[:8]:
                errors = service_levels[service].get('ERROR', 0)
                health = "🔴" if errors > count * 0.1 else "⚠️" if errors > 0 else "✅"
                response += f"{health} <strong>{service}</strong>: {count:,} events"
                if errors > 0:
                    response += f" <span style='color: #e74c3c;'>({errors} errors)</span>"
                response += "<br>"
            
            response += "<br>💡 <a href=\"/search\" style=\"color: #667eea; font-weight: bold; text-decoration: none;\">🔗 Explore services in Search page →</a><br>"
            response += "<br><em>Want to know more about a specific service? Just ask!</em>"
            return response
            
        except Exception as e:
            return f"Had a bit of trouble with that: {str(e)}"
    
    def _analyze_time_based(self, query):
        """Recent activity analysis"""
        try:
            recent_events = self.ledger.list_events(limit=20)
            
            if not recent_events:
                return "No recent activity to show yet. Upload some logs and I'll keep you updated! ⏰"
            
            response = "<strong>📅 Recent Activity</strong><br><br>"
            response += f"Here's what's been happening lately:<br><br>"
            
            for i, event in enumerate(recent_events[:10], 1):
                level = event.get('level', 'INFO')
                service = event.get('service', 'Unknown')
                message = event.get('message', 'No message')[:60]
                
                emoji = '🔴' if level == 'ERROR' else '⚠️' if level == 'WARN' else '✅'
                response += f"{i}. {emoji} <strong>[{level}]</strong> {service}<br>"
                response += f"&nbsp;&nbsp;&nbsp;&nbsp;<em>{message}...</em><br>"
            
            response += "<br>💡 <a href=\"/search\" style=\"color: #667eea; font-weight: bold; text-decoration: none;\">🔗 View more in Search page →</a><br>"
            response += "<br><em>Need to dig deeper? Just ask me to search for something specific!</em>"
            return response
            
        except Exception as e:
            return f"Couldn't fetch recent activity: {str(e)}"
    
    def _show_comprehensive_stats(self, stats):
        """Comprehensive statistics with insights"""
        total_files = stats.get('total_files', 0)
        total_events = stats.get('total_events', 0)
        error_count = stats.get('error_count', 0)
        total_size_mb = stats.get('total_size', 0) / (1024 * 1024)
        
        error_rate = (error_count / total_events * 100) if total_events > 0 else 0
        
        response = "<strong>📊 System Health Dashboard</strong><br><br>"
        
        # Key metrics
        response += "<strong>📈 Key Metrics:</strong><br>"
        response += f"&nbsp;&nbsp;• Log Files: <strong>{total_files:,}</strong><br>"
        response += f"&nbsp;&nbsp;• Total Events: <strong>{total_events:,}</strong><br>"
        response += f"&nbsp;&nbsp;• Data Volume: <strong>{total_size_mb:.2f} MB</strong><br>"
        response += f"&nbsp;&nbsp;• Error Events: <strong>{error_count:,}</strong><br>"
        response += f"&nbsp;&nbsp;• Error Rate: <strong>{error_rate:.2f}%</strong><br><br>"
        
        # Health assessment
        if error_rate > 10:
            health_icon = "🔴"
            health_status = "Needs Attention"
            health_msg = "Your error rate is quite high. I recommend investigating the error patterns."
        elif error_rate > 5:
            health_icon = "⚠️"
            health_status = "Fair"
            health_msg = "There are some errors, but nothing critical. Keep monitoring."
        else:
            health_icon = "✅"
            health_status = "Healthy"
            health_msg = "Everything looks good! Your system is performing well."
        
        response += f"<strong>{health_icon} System Health:</strong> {health_status}<br>"
        response += f"<em>{health_msg}</em><br><br>"
        
        response += "💡 <em>Ask me to 'analyze errors' or 'show services' for more details!</em>"
        return response
    
    def _help_upload_files(self):
        """Upload guidance"""
        return """
            <strong>📤 How to Upload Your Logs</strong><br><br>
            
            Let me walk you through it:<br><br>
            
            <strong>Method 1: Direct File Upload</strong><br>
            1. Click <strong>"Upload"</strong> in the navigation<br>
            2. Drag & drop your log files, or click to browse<br>
            3. Supported formats: .log, .txt, .json<br>
            4. Hit upload and I'll process them automatically!<br><br>
            
            <strong>Method 2: Auto-Fetch with Plugins</strong><br>
            • Configure Azure Blob Storage<br>
            • Set up AWS S3 connections<br>
            • Connect REST APIs<br>
            • Click "Fetch Data" and I'll grab your logs!<br><br>
            
            <strong>✨ Pro Tips:</strong><br>
            • I can handle structured JSON logs beautifully<br>
            • Large files? No problem - I'll process them efficiently<br>
            • Once uploaded, logs are automatically indexed for fast searching<br><br>
            
            Need help with plugins? Just ask!
        """
    
    def _help_search_logs(self):
        """Search guidance"""
        return """
            <strong>🔍 Searching Your Logs Like a Pro</strong><br><br>
            
            The Search page is powered by our <strong>Nexus Agent</strong> with TF-IDF indexing. 
            Here's how to use it:<br><br>
            
            <strong>🎯 Search Techniques:</strong><br>
            • <strong>Keywords:</strong> Just type what you're looking for<br>
            &nbsp;&nbsp;Example: "authentication failed"<br>
            • <strong>Filters:</strong> Narrow down by service, level, time<br>
            • <strong>Combinations:</strong> Mix keywords with filters<br><br>
            
            <strong>💡 Example Searches:</strong><br>
            • "database timeout" → Find DB connection issues<br>
            • "500 error" → Locate server errors<br>
            • "user login" → Track authentication events<br><br>
            
            <strong>🚀 Advanced Tips:</strong><br>
            • Use the time range filter for specific periods<br>
            • Filter by ERROR level to focus on problems<br>
            • Service filter helps isolate microservice issues<br><br>
            
            Try it out and let me know if you need help finding something specific!
        """
    
    def _help_plugins(self):
        """Plugin guidance"""
        return """
            <strong>🔌 Plugin System Guide</strong><br><br>
            
            Plugins let you automatically fetch logs from cloud storage and APIs. 
            It's like having a robot assistant! 🤖<br><br>
            
            <strong>📦 Available Plugins:</strong><br><br>
            
            <strong>1. Azure Blob Storage</strong><br>
            &nbsp;&nbsp;• Perfect for Azure-hosted logs<br>
            &nbsp;&nbsp;• Just paste your SAS token URL<br>
            &nbsp;&nbsp;• I'll auto-detect and fetch your files<br><br>
            
            <strong>2. AWS S3</strong><br>
            &nbsp;&nbsp;• Works with S3 buckets<br>
            &nbsp;&nbsp;• Use presigned URLs<br>
            &nbsp;&nbsp;• Secure and fast<br><br>
            
            <strong>3. REST APIs</strong><br>
            &nbsp;&nbsp;• Any HTTP endpoint with logs<br>
            &nbsp;&nbsp;• Supports authentication tokens<br>
            &nbsp;&nbsp;• Generic and flexible<br><br>
            
            <strong>4. Webhooks</strong><br>
            &nbsp;&nbsp;• Receive logs via POST requests<br>
            &nbsp;&nbsp;• Real-time log ingestion<br><br>
            
            <strong>🎯 How to Use:</strong><br>
            1. Go to Upload page<br>
            2. Choose your plugin type<br>
            3. Enter URL and credentials<br>
            4. Click "Fetch Data" - I'll handle the rest!<br><br>
            
            The system will show you a progress bar while fetching. Cool, right? 😎
        """
    
    def _search_specific_logs(self, query):
        """Handle specific log search requests - performs actual search and returns results with links"""
        try:
            # Extract search terms from the query
            search_terms = self._extract_search_terms(query)
            
            if not search_terms:
                return """
                    I'd be happy to search for you! What exactly are you looking for?<br><br>
                    <strong>Try asking:</strong><br>
                    • "show me authentication logs"<br>
                    • "find database errors"<br>
                    • "search for timeout issues"<br>
                    • "show vm logs"
                """
            
            # Search the database
            all_events = self.ledger.list_events(limit=500)
            
            # Filter events that match search terms
            matching_events = []
            for event in all_events:
                message = (event.get('message') or '').lower()
                service = (event.get('service') or '').lower()
                level = (event.get('level') or '').lower()
                
                # Check if any search term matches
                for term in search_terms:
                    if term in message or term in service or term in level:
                        matching_events.append(event)
                        break
            
            if not matching_events:
                search_url = f"/search?query={'+'.join(search_terms)}"
                return f"""
                    🔍 I searched through all your logs but didn't find any matches for <strong>"{' '.join(search_terms)}"</strong>.<br><br>
                    
                    <strong>Suggestions:</strong><br>
                    • Try different keywords<br>
                    • Check for typos<br>
                    • Use the <a href="{search_url}" style="color: #667eea; font-weight: bold;">Search page</a> for advanced filters<br><br>
                    
                    What else can I help you find?
                """
            
            # Display top results
            results_count = len(matching_events)
            display_count = min(5, results_count)
            search_url = f"/search?query={'+'.join(search_terms)}"
            
            response = f"🎯 <strong>Found {results_count} log entries matching '{' '.join(search_terms)}'</strong><br><br>"
            response += f"<strong>Top {display_count} Results:</strong><br><br>"
            
            for i, event in enumerate(matching_events[:display_count], 1):
                level = event.get('level', 'INFO')
                service = event.get('service', 'Unknown')
                message = event.get('message', 'No message')
                timestamp = event.get('ts_event', '')
                event_id = event.get('id', '')
                
                # Truncate long messages
                display_msg = message if len(message) <= 100 else message[:100] + '...'
                
                # Level emoji
                emoji = '🔴' if level == 'ERROR' else '⚠️' if level == 'WARN' else 'ℹ️' if level == 'INFO' else '🐛'
                
                response += f"{i}. {emoji} <strong>[{level}]</strong> {service}<br>"
                response += f"&nbsp;&nbsp;&nbsp;&nbsp;<em>{display_msg}</em><br>"
                if timestamp:
                    response += f"&nbsp;&nbsp;&nbsp;&nbsp;<small style='color: #666;'>⏰ {timestamp}</small><br>"
                response += "<br>"
            
            if results_count > display_count:
                response += f"<br>📄 <strong>Showing {display_count} of {results_count} results.</strong><br>"
            
            response += f"<br>💡 <a href=\"{search_url}\" style=\"color: #667eea; font-weight: bold; text-decoration: none;\">🔗 View all results in Search page →</a><br>"
            response += "<br><em>Need to refine your search? Just ask me for more specific terms!</em>"
            
            return response
            
        except Exception as e:
            return f"""
                Oops! I had trouble searching for that. 😔<br><br>
                Error: {str(e)}<br><br>
                Try using the <a href="/search" style="color: #667eea; font-weight: bold;">Search page</a> for advanced search capabilities!
            """
    
    def _extract_search_terms(self, query):
        """Extract search keywords from user query"""
        # Remove common question words but keep important terms
        stop_words = ['show', 'me', 'find', 'search', 'for', 'get', 'give', 'display', 'list', 'look', 'the', 'a', 'an', 'of', 'in', 'to', 'and', 'all', 'my']
        
        # Clean and split query
        words = query.lower().split()
        search_terms = [w for w in words if w not in stop_words and len(w) > 1]
        
        # If we have "vm" or similar short but important terms, include them
        if not search_terms:
            # Fallback: include 2-letter words if nothing else found
            search_terms = [w for w in words if w not in stop_words]
        
        return search_terms
    
    def _show_comprehensive_help(self):
        """Comprehensive help menu"""
        return """
            <strong>💬 Everything I Can Help You With</strong><br><br>
            
            <strong>🔍 Log Analysis & Insights:</strong><br>
            • "Show me errors" - Detailed error analysis<br>
            • "What services are running?" - Service activity<br>
            • "Show recent activity" - Latest log events<br>
            • "Give me stats" - System health overview<br><br>
            
            <strong>📚 Application Help:</strong><br>
            • "How do I upload logs?" - Upload guide<br>
            • "How to search?" - Search tips & tricks<br>
            • "Explain plugins" - Plugin system guide<br>
            • "What's on the dashboard?" - Dashboard tour<br><br>
            
            <strong>🎯 My Superpowers:</strong><br>
            • I read and analyze your actual log data<br>
            • I understand natural language questions<br>
            • I provide contextual recommendations<br>
            • I'm available on every page!<br><br>
            
            <strong>💡 Pro Tip:</strong> Just chat with me naturally - 
            I understand conversational questions! No need for formal commands. 😊
        """
    
    def _intelligent_default_response(self, original_message, stats):
        """Smart default response with context awareness"""
        total_events = stats.get('total_events', 0)
        
        if total_events == 0:
            return """
                Hmm, I'm not quite sure what you're looking for, but I'm here to help! 🤔<br><br>
                
                Since you don't have any logs uploaded yet, here's what you can do:<br>
                • Ask me <strong>"how to upload logs"</strong><br>
                • Learn about the <strong>"plugin system"</strong><br>
                • Get a <strong>"tour of the app"</strong><br><br>
                
                Or just ask me <strong>"what can you help with?"</strong> and I'll show you everything!
            """
        else:
            return f"""
                Interesting question! I'm not entirely sure what you mean, but let me help you out. 🤔<br><br>
                
                I can see you have <strong>{total_events:,} log events</strong> in the system. 
                Here's what I can do for you:<br><br>
                
                <strong>Try asking:</strong><br>
                • "Show me errors"<br>
                • "What services are active?"<br>
                • "Show recent activity"<br>
                • "Help me search logs"<br><br>
                
                Or type <strong>"help"</strong> to see all my capabilities!
            """
