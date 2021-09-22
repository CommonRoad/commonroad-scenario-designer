sudo apt-get install sumo sumo-tools sumo-doc
echo "export SUMO_HOME=/usr/share/sumo" >> ~/.bashrc
grep -qxF "export SUMO_HOME=/usr/share/sumo" ~/.zshrc || echo "export SUMO_HOME=/usr/share/sumo" >> ~/.zshrc
echo "export PYTHONPATH=\"$SUMO_HOME/tools:$PYTHONPATH\"" >> ~/.bashrc
grep -qxF "export PYTHONPATH=\"$SUMO_HOME/tools:$PYTHONPATH\"" ~/.zshrc || echo "export PYTHONPATH=\"$SUMO_HOME/tools:$PYTHONPATH\"" >> ~/.zshrc