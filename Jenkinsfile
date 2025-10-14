pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                echo "Checking out code from GitHub..."
                git branch: 'master',
                    url: 'https://github.com/pd1608/ANAproject.git'
            }
        }

        stage('Install Dependencies') {
            steps {
                echo "Installing Python dependencies (netmiko)..."
                // Use 'pip3 install' to ensure it uses the Python 3 environment
                // 'netmiko' is the library needed for the script
                sh 'pip3 install netmiko' 
            }
        }

        stage('Ping Test') {
            steps {
                script {
                    echo "Running ping_test.py directly..."
                    // Note: Based on the previous log, the script was found in the workspace root.
                    // I've adjusted the 'cd' command to assume the script is in the root 
                    // of the checked-out repository, as was implied by the execution environment.
                    sh '''
                    cd $WORKSPACE
                    python3 ping_test.py
                    '''
                    // The original script handles writing results to a file specified within the script itself:
                    // LOG_FILE = "/home/student/lab1/pythonscripts/ping_results.txt"
                    // If the script is modified to output to the console and is expected to fail 
                    // if any ping fails, we can add a simple check here.
                }
            }
        }

        stage('Results') {
            // This stage will only run if the 'Ping Test' stage succeeds
            when {
                expression { currentBuild.result == 'SUCCESS' }
            }
            steps {
                script {
                    // Check if the file exists before trying to display/archive
                    // NOTE: This path assumes the script can write to /home/student/lab1/pythonscripts/
                    // which might not be accessible in the Jenkins agent's environment.
                    // If the script fails due to permission/path issues, this must be corrected
                    // in the Python file to use a relative path like 'ping_results.txt'.
                    def resultFilePath = '/home/student/lab1/pythonscripts/ping_results.txt' 

                    echo "Displaying ping results (if file exists at expected path)..."
                    // Try to cat the file - will fail if path is wrong or permissions denied
                    sh(script: "cat ${resultFilePath}", returnStatus: true) 

                    // Archive the results so they are downloadable from Jenkins
                    archiveArtifacts artifacts: resultFilePath, allowEmpty: true
                }
            }
        }
    }

    post {
        success {
            echo "✅ Ping test completed successfully!"
        }
        failure {
            echo "❌ Ping test failed! Check the console output for the netmiko install step and script errors."
        }
    }
}
