pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                echo "Checking out code from GitHub..."
                git branch: 'master', url: 'https://github.com/pd1608/ANAproject.git'
            }
        }

        stage('Install Dependencies') {
            steps {
                script {
                    echo "Setting up virtual environment and installing netmiko..."
                    sh '''
                        # 1. Create a virtual environment named 'venv' in the workspace
                        python3 -m venv venv
                        # 2. Activate the virtual environment using the universal '.' command and install netmiko
                        # We use '&&' to ensure the install only runs if activation succeeds!
                        . venv/bin/activate && pip install netmiko
                    '''
                }
            }
        }

        stage('Ping Test') {
            steps {
                script {
                    echo "Running ping_test.py inside the virtual environment..."
                    sh '''
                        # 1. Change to the workspace root
                        cd $WORKSPACE
                        # 2. Activate the virtual environment using the universal '.' command
                        . venv/bin/activate
                        # 3. Execute the script using the python binary from the venv
                        python3 ping_test.py
                    '''
                }
            }
        }

        stage('Results') {
            when {
                expression { currentBuild.result == 'SUCCESS' }
            }
            steps {
                script {
                    // NOTE: The Python script hardcodes the log file path.
                    def resultFilePath = '/home/student/lab1/pythonscripts/ping_results.txt'
                    echo "Displaying ping results (if file exists at expected path)..."
                    // Use '|| true' to prevent the pipeline from failing if the file doesn't exist yet
                    sh(script: "cat ${resultFilePath} || true", returnStatus: true)
                    // Archive the results
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
            echo "❌ Ping test failed! Review the console output for errors."
        }
    }
}
