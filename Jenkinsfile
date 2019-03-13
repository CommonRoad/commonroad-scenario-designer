#!groovy
pipeline {
	agent {
		dockerfile {
			dir 'tools/opendrive2lanelet'
		}
	}
	environment{
		my_workspace='tools/opendrive2lanelet'
	}
	stages {
		stage('Install Requirements'){
			steps {
				sh '''
				git clean -fdx
				pyenv versions;
				pyenv global 3.7.1;
				pip install --upgrade pip;
				pip install tox tox-pyenv;'''
			}
		}

		stage('Run py.test') {
			steps {
				sh 'pyenv local 3.6.7 3.7.1'
				sh 'cd "$my_workspace" && tox -e py36 -- --junitxml=junit-{envname}.xml --cov-report xml'
				sh 'cd "$my_workspace" && tox -e py37 -- --junitxml=junit-{envname}.xml --cov-report xml'
			}
		}

		stage('Test code quality'){
			steps {
				sh 'cd "$my_workspace" && tox -e flake8 | tee flake8.log|| true'
				sh 'cd "$my_workspace" && tox -e pylint | tee pylint.log|| true'
			}
		}

		stage('Test sphinx documentation'){
			steps{
				sh 'cd "$my_workspace" && tox -e docs'
			}
		}
	}
	post{
		always{
			junit "**/junit-*.xml"
			recordIssues tool: pyLint(pattern: '**/pylint.log'), unstableTotalAll: 100, unstableTotalHigh:0
			recordIssues tool: sphinxBuild()
			recordIssues tool: flake8(pattern: '**/flake8.log')
			cobertura coberturaReportFile: '**/coverage.xml', autoUpdateHealth: false, autoUpdateStability: false, failUnhealthy: false, failUnstable: false, maxNumberOfBuilds: 0, onlyStable: false

		}
	}
}
