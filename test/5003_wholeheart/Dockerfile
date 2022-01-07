FROM mathiser/nnunet:nnunet_base

COPY . /
RUN ["chmod", "+x", "/main.sh"]
ENTRYPOINT ["bash", "-c", "/main.sh"]
CMD ["bash"]
